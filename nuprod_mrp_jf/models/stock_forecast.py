from odoo import models, fields, api
import json

class StockForecastCache(models.Model):
    _name = 'stock.forecast.cache'
    _description = 'Daily forecast availability cache'
    _rec_name = 'warehouse_id'
    _order = 'date desc'

    warehouse_id = fields.Many2one('stock.warehouse', required=True, ondelete='cascade')
    location_id = fields.Many2one('stock.location', required=True, ondelete='cascade')
    date = fields.Date(required=True, default=fields.Date.context_today)
    data = fields.Text('Serialized Forecast Data', required=True)  # Pickled or JSON-encoded

    @api.model
    def _cron_clear_old_forecast_cache(self):
        """Delete forecast cache entries older than 7 days."""
        limit_date = fields.Date.context_today(self) - timedelta(days=7)
        old_entries = self.search([('date', '<', limit_date)])
        old_entries.unlink()