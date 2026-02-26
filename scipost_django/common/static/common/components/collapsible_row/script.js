class CollapsibleRow {
    constructor(row) {
        this.row = row;
        this.detailsRow = null;
        this.detailsId = `details-${crypto.randomUUID()}`;

        this.init();
    }

    init() {
        this.row.style.cursor = 'pointer';

        this.row.setAttribute('role', 'button');
        this.row.setAttribute('tabindex', '0');
        this.row.setAttribute('aria-expanded',
            this.row.hasAttribute('open') ? 'true' : 'false');
        this.row.setAttribute('aria-controls', this.detailsId);

        this.row.addEventListener('click', () => this.toggle());
        this.row.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.toggle();
            }
        });

        if (this.row.hasAttribute('open')) {
            this.show();
        }
    }

    get open() {
        return this.row.hasAttribute('open');
    }

    set open(value) {
        if (value) this.row.setAttribute('open', '');
        else this.row.removeAttribute('open');

        this.sync();
    }

    toggle() {
        this.open = !this.open;
    }

    sync() {
        const expanded = this.open;
        this.row.setAttribute('aria-expanded', String(expanded));

        if (expanded) {
            this.hideAccordionRows();
            this.show();
        } else {
            this.hide();
        }
    }

    hideAccordionRows() {
        const group = this.row.getAttribute('name');
        if (!group) return;

        const scope = this.row.closest('tbody, table');
        const rows = scope.querySelectorAll(
            `tr[data-collapsible][name="${CSS.escape(group)}"][open]`
        );

        rows.forEach(r => {
            if (r !== this.row) {
                r.removeAttribute('open'); // Must run first, sync will call inf loop.
                r._collapsible?.sync();
            }
        });
    }

    show() {
        // Create the detail row by cloning the template
        if (!this.detailsRow) {
            const template = this.row.querySelector('template[name="tr-details-content"]');
            if (!template) return;

            this.detailsRow = document.createElement('tr');
            this.detailsRow.id = this.detailsId;

            const td = document.createElement('td');
            td.colSpan = this.row.cells.length;
            td.appendChild(template.content.cloneNode(true));

            this.detailsRow.appendChild(td);
            this.row.after(this.detailsRow);

            if (window.htmx) {
                htmx.process(this.detailsRow);
            };
        }

        this.detailsRow.hidden = false;
    }

    hide() {
        if (this.detailsRow) {
            this.detailsRow.hidden = true;
        }
    }
}

/* Upgrade all rows */
function upgradeCollapsibleRows(root = document) {
    root.querySelectorAll('tr[data-collapsible]').forEach(row => {
        if (!row._collapsible) {
            row._collapsible = new CollapsibleRow(row);
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    upgradeCollapsibleRows();
});

document.addEventListener('htmx:afterSettle', () => {
    upgradeCollapsibleRows();
});

