from openerp.osv import osv, fields

class SaleOrder(osv.osv):
    _inherit = 'sale.order'

    def send_one_sale_order_email(self, cr, uid, ids, context=None):
	picking = self.browse(cr, uid, ids[0])
	report_obj = self.pool.get('sale.email.report')
	return report_obj.render(cr, uid, [picking])
