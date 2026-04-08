/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";

patch(ControlButtons.prototype, {
    async onClickPopupSingleField() {
        this.dialog.add(NumberPopup, {
            title: _t("Discount Amount"),
            startingValue: 0,
            getPayload: async (num) => {
                const amount = this.env.utils.parseValidFloat(num.toString());

                const order = this.pos.get_order();
                if (!order) return;

                const product = this.pos.config.discount_product_id;
                if (!product) {
                    this.dialog.add(AlertDialog, {
                        title: _t("No discount product found"),
                        body: _t(
                            "The discount product seems misconfigured. Make sure it is flagged as 'Can be Sold' and 'Available in Point of Sale'."
                        ),
                    });
                    return;
                }

                // Remove existing discount lines
                order.get_orderlines()
                    .filter((line) => line.get_product() === product)
                    .forEach((line) => line.delete());

                // Add a single discount line with the entered amount
                if (amount > 0) {
                    await this.pos.addLineToCurrentOrder(
                        { product_id: product, price_unit: -amount },
                        { merge: false }
                    );
                }
            },
        });
    },
});

