/** @odoo-module **/
console.log("NUprod installed");
import { TaxTotalsComponent } from "@account/components/tax_totals/tax_totals";
import { formatMonetary } from "@web/views/fields/formatters";
import { patch } from "@web/core/utils/patch";

const { onMounted } = owl;

patch(TaxTotalsComponent.prototype, "nuprodFormatData", {
	setup() {
		this._super(...arguments);
	},
	/**
	 * @override
	 */
	formatData(props) {
		let totals = props.value;
		const currencyFmtOpts = {
			currencyId:
				props.record.data.currency_id &&
				props.record.data.currency_id[0],
		};
		let amount_untaxed = totals.amount_untaxed;
		let amount_tax = 0;
		let subtotals = [];
		let amount_to_around = 0;
		for (let subtotal_title of totals.subtotals_order) {
			let amount_total = amount_untaxed + amount_tax;
			subtotals.push({
				name: subtotal_title,
				amount: amount_total,
				formatted_amount: formatMonetary(amount_total, currencyFmtOpts),
			});
			let group = totals.groups_by_subtotal[subtotal_title];
			for (let i in group) {
				amount_tax = amount_tax + group[i].tax_group_amount;
			}
		}
		totals.subtotals = subtotals;
		let amount_total = amount_untaxed + amount_tax;
		totals.amount_total = amount_total;
		totals.formatted_amount_total = formatMonetary(
			amount_total,
			currencyFmtOpts
		);
		let amount_total_converted = parseFloat(
			totals.formatted_amount_total.replace(",", "").replace(" €", "")
		);
		let last_digit = (amount_total_converted * 1000) % 10;
		if (last_digit !== 0) {
			amount_to_around = 10 - last_digit;
			totals.formatted_amount_total = formatMonetary(
				amount_total_converted + amount_to_around / 1000,
				currencyFmtOpts
			);
		}
		for (let group_name of Object.keys(totals.groups_by_subtotal)) {
			let group = totals.groups_by_subtotal[group_name];
			for (let key in group) {
				let formated_tax = formatMonetary(
					group[key].tax_group_amount,
					currencyFmtOpts
				);
				let formated_tax_converted = parseFloat(
					formated_tax.replace(",", "").replace(" €", "")
				);
				let new_formated_tax =
					formated_tax_converted + amount_to_around / 1000;
				group[key].formatted_tax_group_amount = formatMonetary(
					new_formated_tax,
					currencyFmtOpts
				);
				group[key].formatted_tax_group_base_amount = formatMonetary(
					group[key].tax_group_base_amount,
					currencyFmtOpts
				);
			}
		}
		this.totals = totals;
	},
});
