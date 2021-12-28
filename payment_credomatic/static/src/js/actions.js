odoo.define('payment_credomatic.alert_environment_js', (require) => {
    "use strict";

    const Widget = require('web.Widget');
    const core = require('web.core');

    const SyncrhonizedAccounts = Widget.extend({
        template: 'payment_credomatic.alert_environment',
        init(parent, ctx){
            this.state = ctx.state;
            return this._super.apply(this, arguments);
        }
    });

    core.action_registry.add('payment_credomatic.alert_environment_js', SyncrhonizedAccounts)
});
