/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, useRef } from "@odoo/owl";
import { onWillDestroy, useState, useEffect } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

export class SupplierStatement extends Component {

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.searchInputRef = useRef("searchInput");
        this.dropdownRef = useRef("dropdown");

        this.state = useState({
            suppliers: [],
            filteredSuppliers: [],
            selectedSupplier: null,
            selectedSupplierName: '',
            searchQuery: '',
            showDropdown: false,
            dateFrom: this.getFirstDayOfMonth(),
            dateTo: this.getCurrentDate(),
            formattedDateFrom: this.formatDate(this.getFirstDayOfMonth()),
            formattedDateTo: this.formatDate(this.getCurrentDate()),
            statementLines: [],
            totalInvoice: '0.000',
            totalPaid: '0.000',
            totalBalance: '0.000',
            showTable: false,
        });

        onWillStart(async () => {
            await this.loadSuppliers();
        });

        onMounted(() => {
            this.fixScrolling();
            // Add click listener to close dropdown when clicking outside
            document.addEventListener('click', this.handleOutsideClick.bind(this));
        });

        onWillDestroy(() => {
            document.removeEventListener('click', this.handleOutsideClick.bind(this));
        });

        // Use effect to fix scrolling whenever showTable changes
        useEffect(() => {
            if (this.state.showTable) {
                setTimeout(() => this.fixScrolling(), 100);
            }
        }, () => [this.state.showTable]);
    }

    handleOutsideClick(event) {
        if (this.searchInputRef.el && this.dropdownRef.el) {
            if (!this.searchInputRef.el.contains(event.target) &&
                !this.dropdownRef.el.contains(event.target)) {
                this.state.showDropdown = false;
            }
        }
    }

    onSearchInput(ev) {
        const query = ev.target.value.toLowerCase();
        this.state.searchQuery = query;

        // Only search if query has at least 2 characters
        if (query.length < 2) {
            this.state.filteredSuppliers = [];
            this.state.showDropdown = false;
        } else {
            this.state.filteredSuppliers = this.state.suppliers.filter(supplier =>
                supplier.name.toLowerCase().includes(query)
            );
            this.state.showDropdown = this.state.filteredSuppliers.length > 0;
        }
    }

    onSearchFocus() {
        // Only show dropdown if there's a search query with at least 2 characters
        if (this.state.searchQuery && this.state.searchQuery.length >= 2) {
            this.onSearchInput({ target: { value: this.state.searchQuery } });
        }
    }

    selectSupplier(supplier) {
        this.state.selectedSupplier = supplier.id;
        this.state.selectedSupplierName = supplier.name;
        this.state.searchQuery = supplier.name;
        this.state.showDropdown = false;
    }

    clearSelection() {
        this.state.selectedSupplier = null;
        this.state.selectedSupplierName = '';
        this.state.searchQuery = '';
        this.state.filteredSuppliers = [];
        this.state.showDropdown = false;
        if (this.searchInputRef.el) {
            this.searchInputRef.el.focus();
        }
    }

    fixScrolling() {
        // Remove all overflow restrictions from parent containers
        const selectors = [
            '.o_action_manager',
            '.o_action_manager .o_action',
            '.o_content',
            '.o_web_client',
            'body'
        ];

        selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                if (el) {
                    el.style.setProperty('overflow', 'visible', 'important');
                    el.style.setProperty('overflow-y', 'visible', 'important');
                    el.style.setProperty('height', 'auto', 'important');
                    el.style.setProperty('max-height', 'none', 'important');
                }
            });
        });

        // Ensure the container itself is scrollable
        const container = document.querySelector('.supplier-statement-container');
        if (container) {
            container.style.minHeight = '150vh';
            container.style.paddingBottom = '300px';
        }
    }

    getCurrentDate() {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    getFirstDayOfMonth() {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        return `${year}-${month}-01`;
    }

    formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        const options = { year: 'numeric', month: 'long', day: '2-digit' };
        return date.toLocaleDateString('en-US', options);
    }

    async loadSuppliers() {
        try {
            const suppliers = await this.orm.searchRead(
                'res.partner',
                [['supplier_rank', '>', 0]],
                ['id', 'name'],
                { order: 'name' }
            );
            this.state.suppliers = suppliers;
            this.state.filteredSuppliers = []; // Start with empty list
        } catch (error) {
            console.error('Error loading suppliers:', error);
            this.notification.add('Error loading suppliers', { type: 'danger' });
        }
    }

    onDateFromChange(ev) {
        this.state.dateFrom = ev.target.value;
        this.state.formattedDateFrom = this.formatDate(ev.target.value);

        // Validate that from date is not after to date
        if (this.state.dateTo && this.state.dateFrom > this.state.dateTo) {
            this.notification.add('From Date cannot be after To Date', { type: 'warning' });
        }
    }

    onDateToChange(ev) {
        this.state.dateTo = ev.target.value;
        this.state.formattedDateTo = this.formatDate(ev.target.value);

        // Validate that to date is not before from date
        if (this.state.dateFrom && this.state.dateTo < this.state.dateFrom) {
            this.notification.add('To Date cannot be before From Date', { type: 'warning' });
        }
    }

    async loadStatement() {
        if (!this.state.selectedSupplier) {
            this.notification.add('Please select a supplier', { type: 'warning' });
            return;
        }

        if (!this.state.dateFrom || !this.state.dateTo) {
            this.notification.add('Please select both From Date and To Date', { type: 'warning' });
            return;
        }

        if (this.state.dateFrom > this.state.dateTo) {
            this.notification.add('From Date cannot be after To Date', { type: 'warning' });
            return;
        }

        try {
            const result = await rpc('/web/dataset/call_kw', {
                model: 'account.move',
                method: 'get_supplier_statement',
                args: [],
                kwargs: {
                    partner_id: this.state.selectedSupplier,
                    date_from: this.state.dateFrom,
                    date_to: this.state.dateTo,
                }
            });

            this.state.statementLines = result.lines || [];
            this.state.totalInvoice = result.total_invoice || '0.000';
            this.state.totalPaid = result.total_paid || '0.000';
            this.state.totalBalance = result.total_balance || '0.000';
            this.state.showTable = true;

            // Fix scrolling after data loads
            setTimeout(() => {
                this.fixScrolling();
            }, 200);

            if (this.state.statementLines.length === 0) {
                this.notification.add('No outstanding statements found for this supplier in the selected period', {
                    type: 'info'
                });
            }
        } catch (error) {
            console.error('Error loading statement:', error);
            this.notification.add('Error loading statement data', { type: 'danger' });
        }
    }

    async printStatement() {
        if (!this.state.selectedSupplier) {
            this.notification.add('Please select a supplier', { type: 'warning' });
            return;
        }

        try {
            await this.action.doAction({
                type: 'ir.actions.report',
                report_type: 'qweb-pdf',
                report_name: 'outstanding_statement.supplier_statement_report_template',
                report_file: 'outstanding_statement.supplier_statement_report_template',
                context: {
                    active_id: this.state.selectedSupplier,
                    active_ids: [this.state.selectedSupplier],
                    date_from: this.state.dateFrom,
                    date_to: this.state.dateTo,
                },
            });
        } catch (error) {
            console.error('Error printing statement:', error);
            this.notification.add('Error printing statement', { type: 'danger' });
        }
    }

    async exportToExcel() {
        if (!this.state.selectedSupplier) {
            this.notification.add('Please select a supplier', { type: 'warning' });
            return;
        }

        try {
            await this.action.doAction({
                type: 'ir.actions.act_url',
                url: `/web/export/supplier_statement_excel?partner_id=${this.state.selectedSupplier}&date_from=${this.state.dateFrom}&date_to=${this.state.dateTo}`,
                target: 'self',
            });
        } catch (error) {
            console.error('Error exporting to Excel:', error);
            this.notification.add('Error exporting to Excel', { type: 'danger' });
        }
    }
}

SupplierStatement.template = "SupplierStatement";

registry.category("actions").add(
    "supplier_statement",
    SupplierStatement
);