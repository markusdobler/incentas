from flask import render_template, flash, redirect, url_for, Blueprint, request

from wtforms.ext.sqlalchemy.orm import model_form
from flask.ext.wtf import Form

from support import flash_errors

def crud_bp(session, query_factory, fields_whitelist, prefix, model=None,
            model_defaults=None):
    if fields_whitelist:
        fields_whitelist = fields_whitelist + ('csrf_token',)

    def edit_form(element):
        ModelForm = model_form(element.__class__, db_session=session, base_class=Form)
        form = ModelForm(obj=element)
        if fields_whitelist:
            form._fields = dict((k,v) for (k,v) in form._fields.items() if k in fields_whitelist)
        return form

    def create_form(element_class):
        ModelForm = model_form(element_class, db_session=session, base_class=Form)
        form = ModelForm()
        if fields_whitelist:
            form._fields = dict((k,v) for (k,v) in form._fields.items() if k in fields_whitelist)
        return form

    bp = Blueprint("crud%s"%prefix, __name__, url_prefix=prefix)

    @bp.route('/')
    def index(**kwargs):
        query = query_factory(**kwargs)
        descriptions = [(cds['name'], [c.key for c in cds['expr'].columns]) for cds in query.column_descriptions]
        if len(descriptions)>1:
            fields = ['%s.%s'%(subq, key) for (subq, keys) in descriptions for key in keys]
        else:
            fields = [key for (subq, keys) in descriptions for key in keys]
        if fields_whitelist:
            fields = [f for f in fields if f in fields_whitelist]
        return render_template('crud_index.html', query=query, fields=fields,
                               kwargs=kwargs, allow_create=model is not None)

    @bp.route('/edit/<int:id>', methods=['GET','POST'])
    def edit(id, **kwargs):
        element = query_factory(**kwargs).filter_by(id=id).one()
        form = edit_form(element)
        if form.validate_on_submit():
            form.populate_obj(element)
            session.commit()
            flash('Record updated', 'success')
            return redirect(url_for('.index', **kwargs))
        flash_errors(form)
        return render_template('crud_edit.html', form=form)

    @bp.route('/delete/<int:id>', methods=["POST"])
    def delete(id, **kwargs):
        element = query_factory(**kwargs).filter_by(id=id).one()
        session.delete(element)
        session.commit()
        flash('Record deleted', 'success')
        return "record deleted"

    if model:
        @bp.route('/create', methods=['GET','POST'])
        def create(**kwargs):
            form = create_form(model)
            if form.validate_on_submit():
                session.execute(model.__table__.insert().values(model_defaults(form.data)))
                session.commit()
                flash('Record added', 'success')
                return redirect(url_for('.index', **kwargs))
            flash_errors(form)
            return render_template('crud_edit.html', form=form)

    return bp
