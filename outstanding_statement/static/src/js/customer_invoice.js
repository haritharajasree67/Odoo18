/** @odoo-module **/
import { loadJS } from '@web/core/assets';
import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, useRef } from "@odoo/owl";
import { onWillDestroy, useState, useEffect } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

export class CustomerStatement extends Component {

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.customerSelectRef = useRef("customerSelect");
        this.searchInputRef = useRef("searchInput");
        this.dropdownRef = useRef("dropdown");

        this.state = useState({
            customers: [],
            filteredCustomers: [],
            selectedCustomer: null,
            selectedCustomerName: '',
            dateFrom: this.getFirstDayOfMonth(),
            dateTo: this.getCurrentDate(),
            formattedDateFrom: this.formatDate(this.getFirstDayOfMonth()),
            formattedDateTo: this.formatDate(this.getCurrentDate()),
            statementLines: [],
            totalInvoice: '0.000',
            totalReceived: '0.000',
            totalBalance: '0.000',
            showTable: false,
            showDropdown: false,
            searchQuery: '',
        });

        onWillStart(async () => {
            await this.loadCustomers();
        });

        onMounted(() => {
            this.fixScrolling();
            // Add click outside listener
            document.addEventListener('click', this.handleClickOutside.bind(this));
        });

        onWillDestroy(() => {
            document.removeEventListener('click', this.handleClickOutside.bind(this));
        });

        // Use effect to fix scrolling whenever showTable changes
        useEffect(() => {
            if (this.state.showTable) {
                setTimeout(() => this.fixScrolling(), 100);
            }
        }, () => [this.state.showTable]);
    }

    handleClickOutside(event) {
        const dropdown = this.dropdownRef.el;
        const searchInput = this.searchInputRef.el;

        if (dropdown && searchInput &&
            !dropdown.contains(event.target) &&
            !searchInput.contains(event.target)) {
            this.state.showDropdown = false;
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
        const container = document.querySelector('.customer-statement-container');
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

    // Helper to get customer name as string
    getCustomerName(customer) {
        if (!customer) return '';
        // Handle case where name is an array [id, name]
        if (Array.isArray(customer.name)) {
            return customer.name[1] || '';
        }
        // Handle normal string
        return customer.name || '';
    }

    async loadCustomers() {
        try {
            const customers = await this.orm.searchRead(
                'res.partner',
                [['customer_rank', '>', 0]],
                ['id', 'name'],
                { order: 'name' }
            );

            // Normalize customer data
            this.state.customers = customers.map(customer => ({
                id: customer.id,
                name: this.getCustomerName(customer),
                originalName: customer.name
            }));

            this.state.filteredCustomers = this.state.customers;

            console.log('Loaded customers:', this.state.customers.length);
        } catch (error) {
            console.error('Error loading customers:', error);
            this.notification.add('Error loading customers', { type: 'danger' });
        }
    }

    onSearchInput(ev) {
        const query = ev.target.value.toLowerCase();
        this.state.searchQuery = ev.target.value;
        this.state.showDropdown = true;

        if (query === '') {
            this.state.filteredCustomers = this.state.customers;
        } else {
            this.state.filteredCustomers = this.state.customers.filter(customer => {
                const customerName = customer.name || '';
                return customerName.toLowerCase().includes(query);
            });
        }
    }

    onSearchFocus() {
        this.state.showDropdown = true;
        this.state.filteredCustomers = this.state.customers;
    }

    selectCustomer(customer) {
        this.state.selectedCustomer = customer.id;
        this.state.selectedCustomerName = customer.name;
        this.state.searchQuery = customer.name;
        this.state.showDropdown = false;
        console.log('Customer selected:', customer.id, customer.name);
    }

    clearSelection() {
        this.state.selectedCustomer = null;
        this.state.selectedCustomerName = '';
        this.state.searchQuery = '';
        this.state.filteredCustomers = this.state.customers;
        this.state.showDropdown = false;
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
        console.log('=== Load Statement Debug ===');
        console.log('Selected customer:', this.state.selectedCustomer);
        console.log('Date from:', this.state.dateFrom);
        console.log('Date to:', this.state.dateTo);

        if (!this.state.selectedCustomer) {
            this.notification.add('Please select a customer', { type: 'warning' });
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
                method: 'get_customer_statement',
                args: [],
                kwargs: {
                    partner_id: this.state.selectedCustomer,
                    date_from: this.state.dateFrom,
                    date_to: this.state.dateTo,
                }
            });

            this.state.statementLines = result.lines || [];
            this.state.totalInvoice = result.total_invoice || '0.000';
            this.state.totalReceived = result.total_received || '0.000';
            this.state.totalBalance = result.total_balance || '0.000';
            this.state.showTable = true;

            // Fix scrolling after data loads
            setTimeout(() => {
                this.fixScrolling();
            }, 200);

            if (this.state.statementLines.length === 0) {
                this.notification.add('No outstanding statements found for this customer in the selected period', {
                    type: 'info'
                });
            }
        } catch (error) {
            console.error('Error loading statement:', error);
            this.notification.add('Error loading statement data', { type: 'danger' });
        }
    }

    async printStatement() {
        if (!this.state.selectedCustomer) {
            this.notification.add('Please select a customer', { type: 'warning' });
            return;
        }

        try {
            await this.action.doAction({
                type: 'ir.actions.report',
                report_type: 'qweb-pdf',
                report_name: 'outstanding_statement.customer_statement_report',
                data: {
                    partner_id: this.state.selectedCustomer,
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
        if (!this.state.selectedCustomer) {
            this.notification.add('Please select a customer', { type: 'warning' });
            return;
        }

        try {
            await this.action.doAction({
                type: 'ir.actions.act_url',
                url: `/web/export/customer_statement_excel?partner_id=${this.state.selectedCustomer}&date_from=${this.state.dateFrom}&date_to=${this.state.dateTo}`,
                target: 'self',
            });
        } catch (error) {
            console.error('Error exporting to Excel:', error);
            this.notification.add('Error exporting to Excel', { type: 'danger' });
        }
    }
}

CustomerStatement.template = "CustomerStatement";

registry.category("actions").add(
    "customer_statement",
    CustomerStatement
);