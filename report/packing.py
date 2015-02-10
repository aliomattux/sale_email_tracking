import time
from datetime import datetime
from openerp.osv import osv, fields
from pprint import pprint as pp
from openerp.tools.translate import _
from tzlocal import get_localzone
from lxml import etree
from mako import exceptions
from mako.template import Template


class SaleEmailReport(osv.osv_memory):
    _name = 'sale.email.report'


    def render(self, cr, uid, pickings):
        template = Template(filename='/usr/local/openerp/community/sale_email_tracking/report/packing.mako', \
                strict_undefined=True
        )

	functs = {'get_date_created': self._get_date_created,
		  'paginate_items': self._paginate_items,
		  'objects': pickings,
		  'cr': cr,
	}

        html = template.render(**functs)
	self.send_notification(html, pickings[0])
        return True


    def send_notification(self, html, sale):
        from email.MIMEMultipart import MIMEMultipart
        from email.MIMEText import MIMEText
        from email.MIMEImage import MIMEImage
        import smtplib
#	current_date = self.current_date()
	invoice_id = sale.partner_invoice_id
	shipping_id = sale.partner_shipping_id

	if sale.order_email:
	    email = sale.order_email
	    name = sale.partner_id.name
	elif shipping_id.email:
	    email = shipping_id.email
	    name = shipping_id.name
	elif invoice_id.email:
	    email = invoice_id.email
	    name = invoice_id.name
	else:
	    return False
	    
        sender = 'support@bitsoflace.com'
#	receivers = [email]
	receivers = ['kyle.waid@gcotech.com']
	msg = MIMEMultipart()
	msg['Subject'] = 'Your Order: %s ' % sale.name
	msg['From'] = "Customer Service <support@bitsoflace.com>"
#	msg['To'] = "%s <%s>" % (name, email)
	msg['To'] = "%s <%s>" % ('Kyle Waid', 'kyle.waid@gcotech.com')
	body = html
	content = MIMEText(body, 'html')
	msg.attach(content)
        try:
            smtpObj = smtplib.SMTP('localhost')
            smtpObj.sendmail(sender, receivers, msg.as_string())

        except Exception, e:
	    client.captureException()
            print e

	return True


    def _get_date_created(self, picking):
        if picking.create_date and picking.create_date != 'False':
            date_obj = datetime.strptime(picking.create_date, '%Y-%m-%d %H:%M:%S')
            tz = get_localzone()
            dt = tz.localize(date_obj)
            return datetime.strftime(dt, '%m/%d/%Y')

        return ' '


    def prepare_line_val(self, cr, product, move):
	special_order = ' '
	uid = 1

	for route in product.route_ids:
	    if route.name == 'Make To Order':
	        special_order = 'Yes'
		break

        return {
		'qty_order': int(move.product_uos_qty),
		'sku': product.default_code or '',
		'description': product.name or '',
		'unit_price': '$' + "%.2f" % move.price_unit,
		'qty_available': int(product.qty_available),
		'special_order': special_order,
	}


    def _get_components_list(self, cr, line):
	result = []
	for component in line.item.components:
	    result.append(self.prepare_line_val(cr, component.item, component.qty * line.qty))

	return result


    def show_backorder_lines(self, cr, uid, move):
	result = []
        move_obj = self.pool.get('stock.move')
	move_ids = move_obj.search(cr, uid, [('backorder_id', '=', move.order_id.id)])
	if move_ids:
	   for backorder_move in move_obj.browse(cr, uid, move_ids):
	       result.append(self.prepare_line_val(cr, backorder_move.product_id, backorder_move))

	return result


    def _process_lines(self, cr, uid, lines):
	result = []
        for line in lines:
	    result.append(self.prepare_line_val(cr, line.product_id, line))

	result.extend(self.show_backorder_lines(cr, uid, line))
	return result
#	return sorted(result, key=lambda id: id['prime_location'])


    def _paginate_items(self, cr, lines):

	uid = 1
	processed_lines = self._process_lines(cr, uid, lines)

	return processed_lines

