from datetime import date
from datetime import datetime
from datetime import timedelta

from flask import Flask
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from flask.ext.sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config.from_pyfile('config.cfg')
db = SQLAlchemy(app)


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store = db.Column(db.String)
    value = db.Column(db.Float)
    date = db.Column(db.Date)

    def __init__(self, store, date, value):
        self.store = store
        self.date = date
        self.value = value


@app.route('/new', methods=['GET', 'POST'])
def new_invoice():
    if request.method == 'POST' \
            and request.form['store'] \
            and request.form['date'] \
            and request.form['value']:
        invoice = Invoice(
            request.form['store'],
            datetime.strptime(request.form['date'], "%y/%m/%d"),
            request.form['value'],
        )
        db.session.add(invoice)
        db.session.commit()
        return redirect(url_for('invoices'))

    return render_template(
        'new_invoice.html',
        default_date=date.today().strftime("%y/%m/%d")
    )


@app.route('/<int:invoice_id>/edit', methods=['GET', 'POST'])
def edit_invoice(invoice_id):
    invoice_to_edit = Invoice.query.get_or_404(invoice_id)
    if request.method == 'POST' \
            and request.form['store'] \
            and request.form['date'] \
            and request.form['value']:
        invoice_to_edit.store = request.form['store']
        invoice_to_edit.date = datetime.strptime(
            request.form['date'],
            "%y/%m/%d",
        )
        invoice_to_edit.value = request.form['value']
        db.session.add(invoice_to_edit)
        db.session.commit()

        return redirect(url_for('invoices'))
    return render_template('edit_invoice.html', invoice=invoice_to_edit)


@app.route('/<int:invoice_id>/delete', methods=['GET', 'POST'])
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    if request.method == 'POST':
        if 'yes' in request.form:
            db.session.delete(invoice)
            db.session.commit()
            flash('Invoice was deleted')
            return redirect(url_for('invoices'))
        else:
            return redirect(url_for('invoices'))
    return render_template('delete_invoice.html', invoice=invoice)


@app.route('/', defaults={
    'date_from': date.today() - timedelta(days=30),
    'date_to': date.today() + timedelta(days=1),
    'page': 1,
})
@app.route('/<string:date_from>/<string:date_to>/', defaults={'page': 1})
@app.route('/<string:date_from>/<string:date_to>/page/<int:page>')
def invoices(date_from, date_to, page):
    pagination = Invoice.query \
        .filter(Invoice.date.between(date_from, date_to)) \
        .order_by('date') \
        .paginate(page)
    total = 0
    for invoice in pagination.items:
        total += invoice.value

    return render_template(
        'invoices.html',
        date_from=date_from,
        date_to=date_to,
        pagination=pagination,
        total=total,
    )


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page
