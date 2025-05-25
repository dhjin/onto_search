import os
import logging
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import tempfile
from utils.rdf_helper import (
    load_rdf_from_file, 
    execute_sparql_query, 
    get_namespaces,
    get_rdf_classes,
    get_rdf_properties,
    get_rdf_instances,
    validate_sparql_query
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Global variable to store the current graph
current_graph = None
uploaded_file_path = None

# Configure upload settings
ALLOWED_EXTENSIONS = {'rdf', 'owl', 'ttl', 'n3', 'nt', 'trig', 'nq', 'jsonld'}
TEMP_UPLOAD_FOLDER = tempfile.gettempdir()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global current_graph, uploaded_file_path
    
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(TEMP_UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        try:
            current_graph = load_rdf_from_file(file_path)
            uploaded_file_path = file_path
            flash(f'File {filename} uploaded and parsed successfully!', 'success')
            
            # Get basic ontology information
            namespaces = get_namespaces(current_graph)
            classes = get_rdf_classes(current_graph)
            properties = get_rdf_properties(current_graph)
            
            return render_template(
                'index.html', 
                file_loaded=True, 
                filename=filename,
                namespaces=namespaces,
                classes=classes,
                properties=properties
            )
        except Exception as e:
            logger.error(f"Error parsing RDF file: {str(e)}")
            flash(f'Error parsing file: {str(e)}', 'danger')
            return redirect(url_for('index'))
    else:
        flash(f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}', 'danger')
        return redirect(url_for('index'))

@app.route('/load_sample', methods=['POST'])
def load_sample():
    global current_graph, uploaded_file_path
    
    sample_type = request.form.get('sample_type', 'rdf')
    
    if sample_type == 'rdf':
        file_path = 'sample_data/sample.rdf'
    else:
        file_path = 'sample_data/sample.ttl'
    
    try:
        current_graph = load_rdf_from_file(file_path)
        uploaded_file_path = file_path
        flash(f'Sample {sample_type.upper()} file loaded successfully!', 'success')
        
        # Get basic ontology information
        namespaces = get_namespaces(current_graph)
        classes = get_rdf_classes(current_graph)
        properties = get_rdf_properties(current_graph)
        
        return render_template(
            'index.html', 
            file_loaded=True, 
            filename=f"sample.{sample_type}",
            namespaces=namespaces,
            classes=classes,
            properties=properties
        )
    except Exception as e:
        logger.error(f"Error loading sample file: {str(e)}")
        flash(f'Error loading sample file: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/query', methods=['POST'])
def run_query():
    global current_graph
    
    if not current_graph:
        flash('No ontology loaded. Please upload an RDF file first.', 'danger')
        return redirect(url_for('index'))
    
    query = request.form.get('query', '')
    
    if not query:
        flash('Query cannot be empty', 'danger')
        return redirect(url_for('index'))
    
    # Validate the query
    is_valid, error_message = validate_sparql_query(query)
    if not is_valid:
        flash(f'Invalid SPARQL query: {error_message}', 'danger')
        return redirect(url_for('index'))
    
    try:
        results, columns = execute_sparql_query(current_graph, query)
        return render_template(
            'results.html', 
            query=query, 
            results=results, 
            columns=columns
        )
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        flash(f'Error executing query: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/explore_class/<path:class_uri>')
def explore_class(class_uri):
    global current_graph
    
    if not current_graph:
        flash('No ontology loaded. Please upload an RDF file first.', 'danger')
        return redirect(url_for('index'))
    
    try:
        instances = get_rdf_instances(current_graph, class_uri)
        class_name = class_uri.split('/')[-1] if '/' in class_uri else class_uri.split('#')[-1] if '#' in class_uri else class_uri
        
        return render_template(
            'results.html',
            query=f"Instances of class: {class_name}",
            results=instances,
            columns=['subject', 'predicate', 'object']
        )
    except Exception as e:
        logger.error(f"Error exploring class: {str(e)}")
        flash(f'Error exploring class: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/api/suggest_queries', methods=['GET'])
def suggest_queries():
    global current_graph
    
    if not current_graph:
        return jsonify({"error": "No ontology loaded"}), 400
    
    # Create some generic SPARQL queries based on the loaded ontology
    namespaces = get_namespaces(current_graph)
    classes = get_rdf_classes(current_graph)
    
    suggested_queries = []
    
    # Add basic queries
    suggested_queries.append({
        "name": "List all classes",
        "query": """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT DISTINCT ?class ?label
WHERE {
  { ?class a rdfs:Class } UNION { ?class a owl:Class }
  OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?class
        """
    })
    
    suggested_queries.append({
        "name": "List all properties",
        "query": """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT DISTINCT ?property ?label
WHERE {
  { ?property a rdf:Property } UNION { ?property a owl:ObjectProperty } UNION { ?property a owl:DatatypeProperty }
  OPTIONAL { ?property rdfs:label ?label }
}
ORDER BY ?property
        """
    })
    
    # Add class-specific queries if classes are available
    if classes and len(classes) > 0:
        first_class = classes[0]
        class_uri = first_class['uri']
        
        suggested_queries.append({
            "name": f"Instances of {first_class['label'] or first_class['uri'].split('/')[-1]}",
            "query": f"""
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?instance
WHERE {{
  ?instance a <{class_uri}> .
}}
LIMIT 100
            """
        })
    
    return jsonify(suggested_queries)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
