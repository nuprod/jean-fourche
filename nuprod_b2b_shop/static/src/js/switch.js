/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.SwitchB2B = publicWidget.Widget.extend({
    selector: '.custom-switch-toggle',

    events: {
        'change input[type="checkbox"]': '_onToggle',
    },

    _onToggle: function (ev) {
        const checked = ev.currentTarget.checked;
        if (checked) {
            console.log("Vue ON");
            document.body.classList.add('custom-view');
        } else {
            console.log("Vue OFF");
            document.body.classList.remove('custom-view');
        }
    },
});

export default {
    SwitchB2B: publicWidget.registry.SwitchB2B,
};
