from flask import Flask, render_template, request, redirect, url_for, flash
import json
import datetime
from pathlib import Path
import uuid # Bien que uuid ait été importé, il n'était pas utilisé. Je le laisse au cas où.

# Configuration
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True) # Assure que le dossier data existe

TEMPLATES_FILE = DATA_DIR / 'templates.json'
HISTORY_FILE = DATA_DIR / 'history.json'

class TemplateManager:
    def __init__(self, filepath):
        self.filepath = filepath
        self._ensure_file_exists()
        self.templates = self._load()

    def _ensure_file_exists(self):
        if not self.filepath.exists():
            with open(self.filepath, 'w') as f:
                json.dump([], f)

    def _load(self):
        with open(self.filepath, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return [] # Retourne une liste vide si le fichier est corrompu ou vide

    def _save(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.templates, f, indent=2)

    def get_all(self):
        return self.templates

    def get_by_id(self, template_id):
        return next((t for t in self.templates if t['id'] == template_id), None)

    def add(self, name, items):
        # Filtrer les éléments vides
        items = [item for item in items if item.strip()]
        if not name or not items:
            return False # Indique un échec dû à des données manquantes

        template_id = 1
        if self.templates:
            template_id = max(template['id'] for template in self.templates) + 1
            
        new_template = {
            'id': template_id,
            'name': name,
            'items': items
        }
        self.templates.append(new_template)
        self._save()
        return True # Indique le succès

    def delete(self, template_id):
        self.templates = [t for t in self.templates if t['id'] != template_id]
        self._save()

class HistoryManager:
    def __init__(self, filepath):
        self.filepath = filepath
        self._ensure_file_exists()
        self.history = self._load()

    def _ensure_file_exists(self):
        if not self.filepath.exists():
            with open(self.filepath, 'w') as f:
                json.dump([], f)

    def _load(self):
        with open(self.filepath, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def _save(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.history, f, indent=2)

    def get_all_sorted(self):
        # Trier par date (du plus récent au plus ancien)
        return sorted(self.history, key=lambda x: x['date'], reverse=True)

    def add_entry(self, template_id, template_name, template_items, checked_items, comment):
        history_entry_id = 1
        if self.history:
            # Assurer que l'ID est unique, même si des éléments sont supprimés (rare pour l'historique)
            # Ou simplement utiliser len(self.history) + 1 si les ID n'ont pas besoin d'être strictement séquentiels après suppression
            history_entry_id = max(entry.get('id', 0) for entry in self.history) + 1


        history_entry = {
            'id': history_entry_id,
            'template_id': template_id,
            'template_name': template_name,
            'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'items': [{'name': item, 'checked': item in checked_items} for item in template_items],
            'comment': comment
        }
        self.history.append(history_entry)
        self._save()

# Initialisation de l'application Flask
app = Flask(__name__)
app.secret_key = 'checklist_pro_secret_key' # Nécessaire pour les messages flash

# Initialisation des managers
template_manager = TemplateManager(TEMPLATES_FILE)
history_manager = HistoryManager(HISTORY_FILE)

# Routes
@app.route('/', methods=['GET'])
def index():
    templates_data = template_manager.get_all()
    # Adapter pour index.html qui attend 'elements'
    # Il est préférable de garder 'items' dans le modèle de données et de faire la transformation ici si nécessaire
    templates_for_view = []
    for t in templates_data:
        # Crée une copie pour ne pas modifier l'objet original dans template_manager.templates
        template_copy = t.copy()
        template_copy['elements'] = template_copy.get('items', []) 
        templates_for_view.append(template_copy)
    return render_template('index.html', templates=templates_for_view)

@app.route('/create_template', methods=['GET', 'POST'])
def create_template():
    if request.method == 'POST':
        name = request.form.get('name')
        items = request.form.getlist('items')
        
        if template_manager.add(name, items):
            flash('Modèle de checklist créé avec succès!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Le nom et au moins un élément sont requis.', 'danger')
            # Renvoyer les données saisies pour ne pas les perdre
            return render_template('create_template.html', name=name, items=items)
            
    return render_template('create_template.html', name='', items=['']) # Fournir des valeurs par défaut

@app.route('/fill_checklist/<int:template_id>', methods=['GET', 'POST'])
def fill_checklist(template_id):
    template = template_manager.get_by_id(template_id)
    
    if not template:
        flash('Modèle non trouvé', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        checked_items = request.form.getlist('checked_items')
        comment = request.form.get('comment', '')
        
        history_manager.add_entry(
            template_id=template['id'],
            template_name=template['name'],
            template_items=template['items'], # Utiliser 'items' ici
            checked_items=checked_items,
            comment=comment
        )
        
        flash('Checklist enregistrée avec succès!', 'success')
        return redirect(url_for('history_list')) # Renommé pour clarté, voir route history_list
    
    # Assurer que 'items' est passé au template fill_checklist.html
    # Si fill_checklist.html s'attend à 'elements', il faudra l'ajuster ou faire la transformation ici.
    # Pour l'instant, on suppose qu'il utilise 'items' ou que 'template' contient déjà ce qu'il faut.
    return render_template('fill_checklist.html', template=template)

@app.route('/delete_template/<int:template_id>', methods=['POST'])
def delete_template(template_id):
    template_manager.delete(template_id)
    flash('Modèle supprimé avec succès', 'success')
    return redirect(url_for('index'))

@app.route('/history') # Renommé en history_list pour éviter confusion avec le module history
def history_list():
    history_entries = history_manager.get_all_sorted()
    return render_template('history.html', history=history_entries)

if __name__ == '__main__':
    app.run(debug=True)