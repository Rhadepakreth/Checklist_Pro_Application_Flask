from flask import Flask, render_template, request, redirect, url_for, flash
import datetime
from flask_sqlalchemy import SQLAlchemy
import os

# Initialisation de l'application Flask
app = Flask(__name__)
app.secret_key = 'checklist_pro_secret_key' # Nécessaire pour les messages flash

# Configuration de SQLAlchemy
# Créez un dossier 'instance' à la racine de votre projet s'il n'existe pas.
# La base de données SQLite sera stockée là.
instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "checklist_pro.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modèles de base de données
class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # Relation avec TemplateItem: si un Template est supprimé, ses items le sont aussi.
    items = db.relationship('TemplateItem', backref='template', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Template {self.name}>'

class TemplateItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('template.id'), nullable=False)

    def __repr__(self):
        return f'<TemplateItem {self.name}>'

class HistoryEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_id_original = db.Column(db.Integer, nullable=True) # ID du template au moment de la création
    template_name = db.Column(db.String(100), nullable=False) # Nom du template au moment de la création
    date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    comment = db.Column(db.Text, nullable=True)
    # Relation avec HistoryItem
    items = db.relationship('HistoryItem', backref='history_entry', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<HistoryEntry {self.template_name} on {self.date}>'

class HistoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    checked = db.Column(db.Boolean, nullable=False, default=False)
    history_entry_id = db.Column(db.Integer, db.ForeignKey('history_entry.id'), nullable=False)

    def __repr__(self):
        return f'<HistoryItem {self.name} (Checked: {self.checked})>'

# Routes
@app.route('/', methods=['GET'])
def index():
    templates_data = Template.query.order_by(Template.name).all()
    templates_for_view = []
    for t in templates_data:
        templates_for_view.append({
            'id': t.id,
            'name': t.name,
            'elements': [item.name for item in t.items] # 'elements' pour correspondre au template existant
        })
    return render_template('index.html', templates=templates_for_view)

@app.route('/create_template', methods=['GET', 'POST'])
def create_template():
    if request.method == 'POST':
        name = request.form.get('name')
        item_names = [item_name for item_name in request.form.getlist('items') if item_name.strip()]

        if not name or not item_names:
            flash('Le nom du modèle et au moins un élément sont requis.', 'danger')
            return render_template('create_template.html', name=name, items=item_names if item_names else [''])

        new_template = Template(name=name)
        for item_name_str in item_names:
            new_template_item = TemplateItem(name=item_name_str)
            new_template.items.append(new_template_item)
        
        try:
            db.session.add(new_template)
            db.session.commit()
            flash('Modèle de checklist créé avec succès!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du modèle: {str(e)}', 'danger')
            return render_template('create_template.html', name=name, items=item_names)
            
    return render_template('create_template.html', name='', items=[''])

@app.route('/fill_checklist/<int:template_id>', methods=['GET', 'POST'])
def fill_checklist(template_id):
    template = Template.query.get_or_404(template_id)
    
    if request.method == 'POST':
        checked_item_names = request.form.getlist('checked_items')
        comment = request.form.get('comment', '')
        
        # Créer une nouvelle entrée d'historique
        history_entry = HistoryEntry(
            template_id_original=template.id,
            template_name=template.name,
            comment=comment
        )
        
        template_item_names = [item.name for item in template.items]
        for item_name_str in template_item_names:
            history_item = HistoryItem(
                name=item_name_str,
                checked=(item_name_str in checked_item_names)
            )
            history_entry.items.append(history_item)
            
        try:
            db.session.add(history_entry)
            db.session.commit()
            flash('Checklist enregistrée avec succès!', 'success')
            return redirect(url_for('history_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'enregistrement de la checklist: {str(e)}', 'danger')
            # Renvoyer les données pour éviter la perte
            # Préparer les items du template pour la vue
            template_view_items = [{'name': item.name} for item in template.items]
            return render_template('fill_checklist.html', template={'id': template.id, 'name': template.name, 'items': template_view_items}, comment=comment, checked_items=checked_item_names)

    # Pour la méthode GET, préparer les items du template pour la vue
    # fill_checklist.html s'attend à ce que template.items soit une liste de strings ou de dicts avec 'name'
    template_view_items = [{'name': item.name} for item in template.items]
    return render_template('fill_checklist.html', template={'id': template.id, 'name': template.name, 'items': template_view_items})


@app.route('/delete_template/<int:template_id>', methods=['POST'])
def delete_template(template_id):
    template_to_delete = Template.query.get_or_404(template_id)
    try:
        # Suppression en cascade grâce à la relation définie dans le modèle
        db.session.delete(template_to_delete)
        db.session.commit()
        flash('Modèle supprimé avec succès', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression : {str(e)}', 'danger')
    return redirect(url_for('index'))

@app.route('/history')
def history_list():
    # Trier par date (du plus récent au plus ancien)
    history_entries_data = HistoryEntry.query.order_by(HistoryEntry.date.desc()).all()
    
    # Adapter les données pour le template si nécessaire
    # history.html s'attend à ce que chaque entry ait 'items' qui est une liste de dicts {'name': ..., 'checked': ...}
    # Et 'date' formatée.
    history_for_view = []
    for entry in history_entries_data:
        history_for_view.append({
            'id': entry.id,
            'template_name': entry.template_name,
            'date': entry.date.strftime('%Y-%m-%d %H:%M:%S'), # Formater la date
            'items': [{'name': item.name, 'checked': item.checked} for item in entry.items],
            'comment': entry.comment
        })
    return render_template('history.html', history=history_for_view)

@app.route('/edit_template/<int:template_id>', methods=['GET', 'POST'])
def edit_template(template_id):
    template = Template.query.get_or_404(template_id)
    
    if request.method == 'POST':
        template.name = request.form.get('name')
        new_items = [item.strip() for item in request.form.getlist('items') if item.strip()]
        
        # Suppression des anciens éléments
        TemplateItem.query.filter_by(template_id=template_id).delete()
        
        # Ajout des nouveaux éléments
        for item_name in new_items:
            template.items.append(TemplateItem(name=item_name))
        
        try:
            db.session.commit()
            flash('Modèle mis à jour avec succès', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour : {str(e)}', 'danger')
    
    # Pré-remplissage du formulaire
    items = [item.name for item in template.items]
    return render_template('create_template.html', 
                         name=template.name, 
                         items=items,
                         is_edit=True,
                         template_id=template_id)

if __name__ == '__main__':
    # Il est recommandé d'utiliser Alembic pour créer/migrer la base de données.
    # Pour un développement rapide, vous pouvez décommenter la ligne suivante
    # pour créer les tables si elles n'existent pas, mais Alembic est la meilleure pratique.
    # with app.app_context():
    #     db.create_all()
    app.run(debug=True)