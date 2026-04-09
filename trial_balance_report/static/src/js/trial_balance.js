/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class CustomTrialBalance extends Component {

    setup() {
        this.orm    = useService("orm");
        this.action = useService("action");

        this.state = useState({
            lines: [],
            groups: [],
            accounts: [],
            journals: [],
            partners: [],
            accountTags: [],
            showFilters: false,
            filters: {
                dateFrom:         this._isoYearStart(),
                dateTo:           this._isoYearEnd(),
                dateRange:        "this_year",
                targetMoves:      "posted",
                displayAccounts:  "non_zero",
                compareDateFrom:  "",
                compareDateTo:    "",
                selectedAccounts: [],
                selectedJournals: [],
                selectedPartners: [],
                selectedTags:     [],
                selectedGroup:    "all",
            },
            applied:        null,
            expandedGroups: {},
            loading:        false,
            exporting:      false,
            popup: {
                show:        false,
                accountId:   null,
                accountName: "",
                lines:       [],
                loading:     false,
            },
        });

        onMounted(() => { this._applyScrollFix(); });
        onWillUnmount(() => { this._removeScrollFix(); });

        onWillStart(async () => {
            await this._loadMeta();
            await this._loadData();
        });
    }

    // ── Scroll Fix ─────────────────────────────────────────────────────────────
    // Odoo server/Odoo.sh applies `overflow: hidden` and fixed heights on multiple
    // ancestor divs via INLINE styles, which CSS cannot override with !important.
    // Solution: walk UP the DOM from our component and reset every element
    // that is clipping overflow. Restore on unmount so other views aren't broken.
    _applyScrollFix() {
        this._savedStyles = [];

        // Target every known Odoo shell container that clips content
        const selectors = [
            '.o_web_client',
            '.o_action_manager',
            '.o_action',
            '.o_view_controller',
            '.o_content',
            '.o_main_content',
            '.o_component',
            '.o_home_menu_background',
        ];

        selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                const cs = window.getComputedStyle(el);
                // Only patch elements that are actually clipping
                const isClipping = ['hidden', 'clip', 'scroll'].includes(cs.overflowY) ||
                                   ['hidden', 'clip', 'scroll'].includes(cs.overflow);
                const hasFixedH  = cs.height !== 'auto' && parseInt(cs.height) > 0;

                if (isClipping || hasFixedH) {
                    this._savedStyles.push({
                        el,
                        overflow:  el.style.overflow,
                        overflowY: el.style.overflowY,
                        overflowX: el.style.overflowX,
                        height:    el.style.height,
                        maxHeight: el.style.maxHeight,
                        flex:      el.style.flex,
                    });
                    el.style.overflow  = 'visible';
                    el.style.overflowY = 'visible';
                    el.style.overflowX = 'visible';
                    el.style.height    = 'auto';
                    el.style.maxHeight = 'none';
                }
            });
        });

        // Also walk up the DOM tree from our component's actual parent
        const root = document.querySelector('.o_trial_balance_report');
        if (root) {
            let el = root.parentElement;
            while (el && el !== document.documentElement) {
                const cs = window.getComputedStyle(el);
                const clips = ['hidden','clip','scroll'].includes(cs.overflowY) ||
                              ['hidden','clip','scroll'].includes(cs.overflow);
                if (clips) {
                    // Avoid double-saving
                    const alreadySaved = this._savedStyles.some(s => s.el === el);
                    if (!alreadySaved) {
                        this._savedStyles.push({
                            el,
                            overflow:  el.style.overflow,
                            overflowY: el.style.overflowY,
                            overflowX: el.style.overflowX,
                            height:    el.style.height,
                            maxHeight: el.style.maxHeight,
                            flex:      el.style.flex,
                        });
                    }
                    el.style.overflow  = 'visible';
                    el.style.overflowY = 'visible';
                    el.style.height    = 'auto';
                    el.style.maxHeight = 'none';
                }
                el = el.parentElement;
            }
        }

        // Final fallback: make the document itself scrollable
        this._savedHtml = {
            overflow: document.documentElement.style.overflow,
            height:   document.documentElement.style.height,
        };
        this._savedBody = {
            overflow: document.body.style.overflow,
            height:   document.body.style.height,
        };
        document.documentElement.style.overflow = 'auto';
        document.documentElement.style.height   = 'auto';
        document.body.style.overflow            = 'auto';
        document.body.style.height              = 'auto';
    }

    _removeScrollFix() {
        if (this._savedStyles) {
            this._savedStyles.forEach(s => {
                s.el.style.overflow  = s.overflow  || '';
                s.el.style.overflowY = s.overflowY || '';
                s.el.style.overflowX = s.overflowX || '';
                s.el.style.height    = s.height    || '';
                s.el.style.maxHeight = s.maxHeight || '';
                s.el.style.flex      = s.flex      || '';
            });
        }
        if (this._savedHtml) {
            document.documentElement.style.overflow = this._savedHtml.overflow || '';
            document.documentElement.style.height   = this._savedHtml.height   || '';
        }
        if (this._savedBody) {
            document.body.style.overflow = this._savedBody.overflow || '';
            document.body.style.height   = this._savedBody.height   || '';
        }
    }

    // ── Date helpers ──────────────────────────────────
    _isoYearStart() { return `${new Date().getFullYear()}-01-01`; }
    _isoYearEnd()   { return `${new Date().getFullYear()}-12-31`; }

    _isoToDisplay(iso) {
        if (!iso) return "";
        const [y, m, d] = iso.split("-");
        return `${d}/${m}/${y}`;
    }

    _isoFmt(d) {
        return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
    }

    // ── Meta loading ──────────────────────────────────
    async _loadMeta() {
        const [groups, accounts, journals, partners, tags] = await Promise.all([
            this.orm.searchRead("account.group", [], ["id", "name", "code_prefix_start"], { order: "code_prefix_start asc" }),
            this.orm.searchRead("account.account", [["deprecated", "=", false]], ["id", "name", "code"], { order: "code asc" }),
            this.orm.searchRead("account.journal", [], ["id", "name"]),
            this.orm.searchRead("res.partner", [["active", "=", true]], ["id", "name"], { limit: 200 }),
            this.orm.searchRead("account.account.tag", [], ["id", "name"]),
        ]);
        const strId = list => list.map(r => ({ ...r, id: String(r.id) }));
        this.state.groups      = strId(groups);
        this.state.accounts    = strId(accounts);
        this.state.journals    = strId(journals);
        this.state.partners    = strId(partners);
        this.state.accountTags = strId(tags);
    }

    // ── Main data loading ─────────────────────────────
    async _loadData() {
        this.state.loading = true;
        const f = this.state.applied || this.state.filters;

        const stateFilter =
            f.targetMoves === "posted" ? [["move_id.state", "=", "posted"]] :
            f.targetMoves === "draft"  ? [["move_id.state", "=", "draft"]]  : [];

        const journalFilter = f.selectedJournals?.length ? [["journal_id", "in", f.selectedJournals]] : [];
        const partnerFilter = f.selectedPartners?.length ? [["partner_id", "in", f.selectedPartners]] : [];
        const common = [...stateFilter, ...journalFilter, ...partnerFilter];

        const accDomain = [["deprecated", "=", false]];
        if (f.selectedAccounts?.length) accDomain.push(["id", "in", f.selectedAccounts]);
        if (f.selectedGroup && f.selectedGroup !== "all")
            accDomain.push(["group_id", "=", Number(f.selectedGroup)]);

        const [fetchedAccounts, initRows, periodRows] = await Promise.all([
            this.orm.searchRead("account.account", accDomain, ["id", "name", "code", "group_id"], { order: "code asc" }),
            this.orm.readGroup("account.move.line",
                [...common, ...(f.dateFrom ? [["date", "<", f.dateFrom]] : [])],
                ["account_id", "debit", "credit"], ["account_id"]),
            this.orm.readGroup("account.move.line",
                [...common,
                 ...(f.dateFrom ? [["date", ">=", f.dateFrom]] : []),
                 ...(f.dateTo   ? [["date", "<=", f.dateTo]]   : [])],
                ["account_id", "debit", "credit"], ["account_id"]),
        ]);

        const initMap = {}, periodMap = {};
        for (const r of initRows)   initMap[r.account_id[0]]   = { debit: r.debit, credit: r.credit };
        for (const r of periodRows) periodMap[r.account_id[0]] = { debit: r.debit, credit: r.credit };

        let lines = fetchedAccounts.map(acc => {
            const init   = initMap[acc.id]   || { debit: 0, credit: 0 };
            const period = periodMap[acc.id] || { debit: 0, credit: 0 };
            const initNet = init.debit - init.credit;
            const periodNet = period.debit - period.credit;
            const endingNet = initNet + periodNet;
            return {
                id: acc.id, code: acc.code, name: acc.name,
                groupId:   acc.group_id ? acc.group_id[0] : null,
                groupName: acc.group_id ? acc.group_id[1] : "Ungrouped",
                initialDebit:   initNet > 0 ?  initNet : 0,
                initialCredit:  initNet < 0 ? -initNet : 0,
                initialBalance: initNet,
                ytdDebit:    periodNet > 0 ?  periodNet : 0,
                ytdCredit:   periodNet < 0 ? -periodNet : 0,
                ytdBalance:  periodNet,
                endingDebit:   endingNet > 0 ?  endingNet : 0,
                endingCredit:  endingNet < 0 ? -endingNet : 0,
                endingBalance: endingNet,
            };
        });

        if (f.displayAccounts === "non_zero")
            lines = lines.filter(l => Math.abs(l.initialBalance) >= 0.0005 || Math.abs(l.ytdBalance) >= 0.0005);
        else if (f.displayAccounts === "balance_non_zero")
            lines = lines.filter(l => Math.abs(l.endingBalance) >= 0.0005);

        this.state.lines = lines;
        const newExpanded = {};
        [...new Set(lines.map(l => l.groupName))].forEach(g => { newExpanded[g] = false; });
        this.state.expandedGroups = newExpanded;
        this.state.loading = false;
    }

    get groupedLines() {
        const r = {};
        for (const l of this.state.lines) {
            if (!r[l.groupName]) r[l.groupName] = [];
            r[l.groupName].push(l);
        }
        return r;
    }

    get groupTotals() {
        const t = {};
        for (const [g, lines] of Object.entries(this.groupedLines)) {
            t[g] = lines.reduce((a, l) => ({
                initialDebit:  a.initialDebit  + l.initialDebit,
                initialCredit: a.initialCredit + l.initialCredit,
                ytdDebit:      a.ytdDebit      + l.ytdDebit,
                ytdCredit:     a.ytdCredit     + l.ytdCredit,
                endingDebit:   a.endingDebit   + l.endingDebit,
                endingCredit:  a.endingCredit  + l.endingCredit,
            }), { initialDebit:0, initialCredit:0, ytdDebit:0, ytdCredit:0, endingDebit:0, endingCredit:0 });
        }
        return t;
    }

    get grandTotal() {
        return this.state.lines.reduce((a, l) => ({
            initialDebit:  a.initialDebit  + l.initialDebit,
            initialCredit: a.initialCredit + l.initialCredit,
            ytdDebit:      a.ytdDebit      + l.ytdDebit,
            ytdCredit:     a.ytdCredit     + l.ytdCredit,
            endingDebit:   a.endingDebit   + l.endingDebit,
            endingCredit:  a.endingCredit  + l.endingCredit,
        }), { initialDebit:0, initialCredit:0, ytdDebit:0, ytdCredit:0, endingDebit:0, endingCredit:0 });
    }

    get hasActiveFilters() {
        const f = this.state.applied;
        if (!f) return false;
        return f.selectedAccounts.length || f.selectedJournals.length ||
               f.selectedPartners.length || f.selectedTags.length    ||
               f.selectedGroup !== "all" || f.targetMoves !== "posted" ||
               f.displayAccounts !== "non_zero";
    }

    get appliedDateLabel() {
        const f = this.state.applied || this.state.filters;
        return `${this._isoToDisplay(f.dateFrom)} → ${this._isoToDisplay(f.dateTo)}`;
    }

    toggleFilters() { this.state.showFilters = !this.state.showFilters; }
    closeFilters()  { this.state.showFilters = false; }
    toggleGroup(g)  { this.state.expandedGroups[g] = !this.state.expandedGroups[g]; }

    onFilterChange(field, ev) {
        this.state.filters[field] = ev.target.value;
        if (field === "dateRange") {
            const yr = new Date().getFullYear();
            const q  = Math.floor(new Date().getMonth() / 3);
            const m  = new Date().getMonth();
            const ranges = {
                this_year:    [`${yr}-01-01`,   `${yr}-12-31`],
                last_year:    [`${yr-1}-01-01`, `${yr-1}-12-31`],
                this_quarter: [this._isoFmt(new Date(yr, q*3, 1)),  this._isoFmt(new Date(yr, q*3+3, 0))],
                this_month:   [this._isoFmt(new Date(yr, m, 1)),    this._isoFmt(new Date(yr, m+1, 0))],
            };
            if (ranges[ev.target.value])
                [this.state.filters.dateFrom, this.state.filters.dateTo] = ranges[ev.target.value];
        }
    }

    onMultiSelectChange(field, ev) {
        this.state.filters[field] = Array.from(ev.target.selectedOptions).map(o => o.value);
    }

    async applyFilters() {
        this.state.applied = { ...this.state.filters };
        this.state.showFilters = false;
        await this._loadData();
    }

    async resetFilters() {
        this.state.filters = {
            dateFrom: this._isoYearStart(), dateTo: this._isoYearEnd(),
            dateRange: "this_year", targetMoves: "posted", displayAccounts: "non_zero",
            compareDateFrom: "", compareDateTo: "",
            selectedAccounts: [], selectedJournals: [], selectedPartners: [],
            selectedTags: [], selectedGroup: "all",
        };
        this.state.applied = null;
        await this._loadData();
    }

    async openJournalItems(acc) {
        this.state.popup.show        = true;
        this.state.popup.accountId   = acc.id;
        this.state.popup.accountName = acc.code + " " + acc.name;
        this.state.popup.lines       = [];
        this.state.popup.loading     = true;

        const f = this.state.applied || this.state.filters;
        const domain = [["account_id", "=", Number(acc.id)]];
        if (f.targetMoves === "posted") domain.push(["move_id.state", "=", "posted"]);
        if (f.targetMoves === "draft")  domain.push(["move_id.state", "=", "draft"]);
        if (f.dateFrom) domain.push(["date", ">=", f.dateFrom]);
        if (f.dateTo)   domain.push(["date", "<=", f.dateTo]);
        if (f.selectedJournals?.length) domain.push(["journal_id", "in", f.selectedJournals.map(Number)]);
        if (f.selectedPartners?.length) domain.push(["partner_id", "in", f.selectedPartners.map(Number)]);

        this.state.popup.lines = await this.orm.searchRead(
            "account.move.line", domain,
            ["date", "move_id", "name", "partner_id", "journal_id", "debit", "credit"],
            { order: "date asc", limit: 500 }
        );
        this.state.popup.loading = false;
    }

    openMoveForm(moveId) {
        if (!moveId) return;
        this.action.doAction({
            type: "ir.actions.act_window", res_model: "account.move",
            res_id: moveId, views: [[false, "form"]], target: "current",
        });
    }

    closePopup() { this.state.popup.show = false; }

    formatAmount(val) {
        if (Math.abs(val) < 0.0005) return "0.000 BD";
        return val.toFixed(3) + " BD";
    }

    _buildExportRows() {
        const headers = ["Account Group","Code","Account Name",
            "Init Debit","Init Credit","Period Debit","Period Credit","End Debit","End Credit"];
        const rows = [headers];
        const fmt = v => v.toFixed(3);
        for (const [group, lines] of Object.entries(this.groupedLines)) {
            for (const l of lines)
                rows.push([group, l.code, l.name,
                    fmt(l.initialDebit), fmt(l.initialCredit),
                    fmt(l.ytdDebit),     fmt(l.ytdCredit),
                    fmt(l.endingDebit),  fmt(l.endingCredit)]);
            const t = this.groupTotals[group];
            rows.push([`TOTAL: ${group}`,"","",
                fmt(t.initialDebit), fmt(t.initialCredit),
                fmt(t.ytdDebit),     fmt(t.ytdCredit),
                fmt(t.endingDebit),  fmt(t.endingCredit)]);
        }
        const g = this.grandTotal;
        rows.push(["GRAND TOTAL","","",
            fmt(g.initialDebit), fmt(g.initialCredit),
            fmt(g.ytdDebit),     fmt(g.ytdCredit),
            fmt(g.endingDebit),  fmt(g.endingCredit)]);
        return rows;
    }

    async downloadXlsx() {
        this.state.exporting = true;
        try {
            if (!window.XLSX) await new Promise((res,rej)=>{const s=document.createElement("script");s.src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js";s.onload=res;s.onerror=rej;document.head.appendChild(s);});
            const rows = this._buildExportRows();
            const ws = window.XLSX.utils.aoa_to_sheet(rows);
            ws["!cols"] = [{wch:32},{wch:12},{wch:36},{wch:14},{wch:14},{wch:14},{wch:14},{wch:14},{wch:14}];
            const wb = window.XLSX.utils.book_new();
            window.XLSX.utils.book_append_sheet(wb, ws, "Trial Balance");
            const f = this.state.applied || this.state.filters;
            window.XLSX.writeFile(wb, `Trial_Balance_${f.dateFrom}_${f.dateTo}.xlsx`);
        } finally { this.state.exporting = false; }
    }

    async downloadPdf() {
        this.state.exporting = true;
        try {
            if (!window.jspdf) await new Promise((res,rej)=>{const s=document.createElement("script");s.src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js";s.onload=res;s.onerror=rej;document.head.appendChild(s);});
            if (!window.jspdf.jsPDF.prototype.autoTable) await new Promise((res,rej)=>{const s=document.createElement("script");s.src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.8.2/jspdf.plugin.autotable.min.js";s.onload=res;s.onerror=rej;document.head.appendChild(s);});
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF({ orientation: "landscape", unit: "mm", format: "a4" });
            const f = this.state.applied || this.state.filters;
            doc.setFontSize(16); doc.setTextColor(113,75,103); doc.text("Trial Balance",14,16);
            doc.setFontSize(9);  doc.setTextColor(100,100,100);
            doc.text(`Date: ${this._isoToDisplay(f.dateFrom)} to ${this._isoToDisplay(f.dateTo)}   |   Moves: ${f.targetMoves==="posted"?"Posted Only":"All Entries"}`,14,23);
            const rows = this._buildExportRows();
            doc.autoTable({
                head:[rows[0]], body:rows.slice(1), startY:28, theme:"grid",
                styles:{fontSize:7,cellPadding:1.8},
                headStyles:{fillColor:[113,75,103],textColor:255,fontStyle:"bold",halign:"center"},
                columnStyles:{0:{cellWidth:36},1:{cellWidth:18},2:{cellWidth:42},3:{cellWidth:22,halign:"right"},4:{cellWidth:22,halign:"right"},5:{cellWidth:22,halign:"right"},6:{cellWidth:22,halign:"right"},7:{cellWidth:22,halign:"right"},8:{cellWidth:22,halign:"right"}},
                didParseCell(d){const l=String(d.row.raw?.[0]||"");if(l.startsWith("TOTAL:")){d.cell.styles.fillColor=[237,233,254];d.cell.styles.fontStyle="bold";}else if(l==="GRAND TOTAL"){d.cell.styles.fillColor=[113,75,103];d.cell.styles.textColor=[255,255,255];d.cell.styles.fontStyle="bold";}},
            });
            doc.save(`Trial_Balance_${f.dateFrom}_${f.dateTo}.pdf`);
        } finally { this.state.exporting = false; }
    }
}

CustomTrialBalance.template = "CustomTrialBalance";
registry.category("actions").add("trial_balance_dynamic_report", CustomTrialBalance);