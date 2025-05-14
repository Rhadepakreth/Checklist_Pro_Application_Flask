from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import os
import datetime
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'checklist_pro_secret_key'  # Nécessaire pour les messages flash

# Assurons-nous que le dossier data existe
data_dir = Path('data')
data_dir.mkdir(exist_ok=True)

# Chemins des fichiers de données
templates_file = data_dir / 'templates.json'
history_file = data_dir / 'history.json'

# Initialisation des fichiers s'ils n'existent pas
if not templates_file.exists():
    with open(templates_file, 'w') as f:
        json.dump([], f)

if not history_file.exists():
    with open(history_file, 'w') as f:
        json.dump([], f)

# Fonctions utilitaires
def load_templates():
    with open(templates_file, 'r') as f:
        return json.load(f)

def save_templates(templates):
    with open(templates_file, 'w') as f:
        json.dump(templates, f, indent=2)

def load_history():
    with open(history_file, 'r') as f:
        return json.load(f)

def save_history(history):
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)

# Routes
@app.route('/')
def index():
    templates = load_templates()
    # In the index route
    for template in templates:
        template['elements'] = template['items']  # Create a new key with the same data
    return render_template('index.html', templates=templates)

@app.route('/create_template', methods=['GET', 'POST'])
def create_template():
    if request.method == 'POST':
        name = request.form.get('name')
        items = request.form.getlist('items')
        
        # Filtrer les éléments vides
        items = [item for item in items if item.strip()]
        
        if not name or not items:
            flash('Le nom et au moins un élément sont requis', 'danger')
            return render_template('create_template.html')
        
        templates = load_templates()
        
        # Générer un ID unique
        template_id = 1
        if templates:
            template_id = max(template['id'] for template in templates) + 1
            
        new_template = {
            'id': template_id,
            'name': name,
            'items': items
        }
        
        templates.append(new_template)
        save_templates(templates)
        
        flash('Modèle de checklist créé avec succès!', 'success')
        return redirect(url_for('index'))
    
    return render_template('create_template.html')

@app.route('/fill_checklist/<int:template_id>', methods=['GET', 'POST'])
def fill_checklist(template_id):
    templates = load_templates()
    template = next((t for t in templates if t['id'] == template_id), None)
    
    if not template:
        flash('Modèle non trouvé', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        checked_items = request.form.getlist('checked_items')
        comment = request.form.get('comment', '')
        
        history = load_history()
        
        # Créer un enregistrement d'historique
        history_entry = {
            'id': len(history) + 1,
            'template_id': template_id,
            'template_name': template['name'],
            'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'items': [{'name': item, 'checked': item in checked_items} for item in template['items']],
            'comment': comment
        }
        
        history.append(history_entry)
        save_history(history)
        
        flash('Checklist enregistrée avec succès!', 'success')
        return redirect(url_for('history'))
    
    return render_template('fill_checklist.html', template=template)

@app.route('/history')
def history():
    history_entries = load_history()
    # Trier par date (du plus récent au plus ancien)
    history_entries.sort(key=lambda x: x['date'], reverse=True)
    return render_template('history.html', history=history_entries)

if __name__ == '__main__':
    app.run(debug=True)