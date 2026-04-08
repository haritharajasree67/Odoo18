/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class BankBook extends Component {

    setup() {
        this.action     = useService("action");
        this.orm        = useService("orm");
        this.filterWrap = useRef("filterWrap");

        this.state = useState({
            date_from: '',      // ← empty by default → show all data
            date_to:   '',      // ← empty by default → show all data
            target_move: 'posted', sortby: 'sort_date',
            display_account: 'movement', initial_balance: false,
            available_journals: [], selected_journal_ids: [],
            available_accounts: [], selected_account_ids: [],
            accounts: [], loading: false, pdfLoading: false, hasSearched: false,
            error: null, showFilters: false,
        });

        onWillStart(async () => {
            await Promise.all([this._loadJournals(), this._loadBankAccounts()]);
            await this._fetchData();
        });

        onMounted(() => {
            document.addEventListener('click', this._onDocClick.bind(this));
        });
    }

    _onDocClick(e) {
        const wrap = this.filterWrap?.el;
        if (wrap && !wrap.contains(e.target)) this.state.showFilters = false;
    }

    async _loadJournals() {
        try {
            const j = await this.orm.searchRead('account.journal', [], ['id','name','code','type'], { order: 'name asc' });
            this.state.available_journals   = j;
            this.state.selected_journal_ids = j.map(x => x.id);
        } catch(e) { console.error(e); }
    }

    async _loadBankAccounts() {
        try {
            const bj = await this.orm.searchRead('account.journal', [['type','=','bank']], ['id','default_account_id']);
            const bankIds = new Set(bj.filter(j => j.default_account_id).map(j => j.default_account_id[0]));
            const all = await this.orm.searchRead('account.account', [], ['id','name','code'], { order: 'code asc' });
            this.state.available_accounts   = all;
            this.state.selected_account_ids = bankIds.size > 0 ? [...bankIds] : all.map(a => a.id);
        } catch(e) { console.error(e); }
    }

    async _fetchData() {
        this.state.loading = true; this.state.hasSearched = true; this.state.error = null;
        try {
            const r = await rpc('/bank_book/get_data', {
                date_from:       this.state.date_from || false,
                date_to:         this.state.date_to   || false,
                target_move:     this.state.target_move,
                sortby:          this.state.sortby,
                display_account: this.state.display_account,
                initial_balance: this.state.initial_balance,
                journal_ids:     this.state.selected_journal_ids,
                account_ids:     this.state.selected_account_ids,
            });
            if (r?.status === 'ok') { this.state.accounts = r.data || []; }
            else { this.state.error = r?.message || 'Server error'; this.state.accounts = []; }
        } catch(e) { this.state.error = e.message || 'Failed'; this.state.accounts = []; }
        finally { this.state.loading = false; }
    }

    onToggleFilters() { this.state.showFilters = !this.state.showFilters; }
    onFieldChange(f, v) { this.state[f] = v; }
    onJournalToggle(id, checked) {
        const ids = this.state.selected_journal_ids;
        this.state.selected_journal_ids = checked ? [...new Set([...ids, id])] : ids.filter(x => x !== id);
    }
    onAccountToggle(id, checked) {
        const ids = this.state.selected_account_ids;
        this.state.selected_account_ids = checked ? [...new Set([...ids, id])] : ids.filter(x => x !== id);
    }
    async onApply() { this.state.showFilters = false; await this._fetchData(); }

    async onPrintPDF() {
        this.state.pdfLoading = true;
        try {
            const r = await rpc('/bank_book/get_pdf', {
                date_from:       this.state.date_from || false,
                date_to:         this.state.date_to   || false,
                target_move:     this.state.target_move,
                sortby:          this.state.sortby,
                display_account: this.state.display_account,
                initial_balance: this.state.initial_balance,
                journal_ids:     this.state.selected_journal_ids,
                account_ids:     this.state.selected_account_ids,
            });
            if (r?.status === 'ok') {
                const a = document.createElement('a');
                a.href = r.url; a.download = r.filename || 'bank_book.pdf';
                document.body.appendChild(a); a.click(); document.body.removeChild(a);
            } else {
                console.error('PDF error:', r?.message);
                alert('PDF generation failed: ' + (r?.message || 'Check Odoo logs.'));
            }
        } catch(e) {
            console.error(e);
            alert('PDF generation failed: ' + e.message);
        } finally {
            this.state.pdfLoading = false;
        }
    }

    async onPrintXLSX() {
        try {
            const r = await rpc('/bank_book/get_xlsx', {
                date_from:       this.state.date_from || false,
                date_to:         this.state.date_to   || false,
                target_move:     this.state.target_move,
                sortby:          this.state.sortby,
                display_account: this.state.display_account,
                initial_balance: this.state.initial_balance,
                journal_ids:     this.state.selected_journal_ids,
                account_ids:     this.state.selected_account_ids,
            });
            if (r?.status === 'ok') {
                const a = document.createElement('a');
                a.href = r.url; a.download = r.filename || 'bank_book.xlsx';
                document.body.appendChild(a); a.click(); document.body.removeChild(a);
            }
        } catch(e) { console.error(e); }
    }

    formatAmount(v) {
        return new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(parseFloat(v) || 0);
    }
}

BankBook.template = "BankBook";
registry.category("actions").add("bank_book", BankBook);