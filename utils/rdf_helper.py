import logging
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, RDFS, OWL
from rdflib.plugins.sparql.parser import parseQuery
from rdflib.plugins.sparql.algebra import translateQuery

logger = logging.getLogger(__name__)

def load_rdf_from_file(file_path):
    """
    Load RDF data from a file into a graph
    
    Args:
        file_path (str): Path to the RDF file
        
    Returns:
        Graph: RDFLib Graph object with the loaded data
    """
    g = Graph()
    # Try to guess the format from file extension
    format_map = {
        '.rdf': 'xml',
        '.owl': 'xml',
        '.ttl': 'turtle',
        '.n3': 'n3',
        '.nt': 'nt',
        '.trig': 'trig',
        '.nq': 'nquads',
        '.jsonld': 'json-ld'
    }
    
    file_extension = file_path[file_path.rfind('.'):].lower() if '.' in file_path else ''
    format_name = format_map.get(file_extension, 'xml')  # Default to XML
    
    try:
        g.parse(file_path, format=format_name)
        logger.info(f"Loaded {len(g)} triples from {file_path}")
        return g
    except Exception as e:
        # If the first format failed, try other formats
        if format_name != 'xml':
            try:
                g = Graph()
                g.parse(file_path, format='xml')
                logger.info(f"Loaded {len(g)} triples from {file_path} using XML format")
                return g
            except Exception:
                pass
        
        if format_name != 'turtle':
            try:
                g = Graph()
                g.parse(file_path, format='turtle')
                logger.info(f"Loaded {len(g)} triples from {file_path} using Turtle format")
                return g
            except Exception:
                pass
        
        # If all attempts failed, raise the original exception
        logger.error(f"Failed to parse RDF file: {str(e)}")
        raise

def execute_sparql_query(graph, query_string):
    """
    Execute a SPARQL query on the given graph
    
    Args:
        graph (Graph): RDFLib Graph to query
        query_string (str): SPARQL query string
        
    Returns:
        tuple: (results, columns) where results is a list of result rows and columns is a list of column names
    """
    try:
        query_results = graph.query(query_string)
        
        # Extract column names from query results
        columns = query_results.vars
        
        # Convert results to a list of dictionaries
        results = []
        for row in query_results:
            result_row = []
            for col in columns:
                cell_value = row.get(col)
                # Convert to string for display
                if cell_value is not None:
                    result_row.append(str(cell_value))
                else:
                    result_row.append('')
            results.append(result_row)
            
        return results, columns
    except Exception as e:
        logger.error(f"Error executing SPARQL query: {str(e)}")
        raise

def validate_sparql_query(query_string):
    """
    Validate a SPARQL query string
    
    Args:
        query_string (str): SPARQL query to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Parse the query
        parsed_query = parseQuery(query_string)
        # Translate to SPARQL algebra
        translateQuery(parsed_query)
        return True, None
    except Exception as e:
        return False, str(e)

def get_namespaces(graph):
    """
    Get all namespaces defined in the graph
    
    Args:
        graph (Graph): RDFLib Graph
        
    Returns:
        list: List of namespace dictionaries with prefix and URI
    """
    namespaces = []
    for prefix, namespace in graph.namespaces():
        namespaces.append({
            'prefix': prefix,
            'uri': namespace
        })
    return namespaces

def get_rdf_classes(graph):
    """
    Get all classes defined in the graph
    
    Args:
        graph (Graph): RDFLib Graph
        
    Returns:
        list: List of class dictionaries with URI and label
    """
    classes = []
    
    # Query for RDFS and OWL classes
    for class_uri in set(
        list(graph.subjects(RDF.type, RDFS.Class)) + 
        list(graph.subjects(RDF.type, OWL.Class))
    ):
        if isinstance(class_uri, URIRef):
            # Get label if available
            label = None
            for label_obj in graph.objects(class_uri, RDFS.label):
                label = str(label_obj)
                break
                
            classes.append({
                'uri': class_uri,
                'label': label
            })
    
    return classes

def get_rdf_properties(graph):
    """
    Get all properties defined in the graph
    
    Args:
        graph (Graph): RDFLib Graph
        
    Returns:
        list: List of property dictionaries with URI and label
    """
    properties = []
    
    # Query for RDF properties and OWL properties
    for prop_uri in set(
        list(graph.subjects(RDF.type, RDF.Property)) + 
        list(graph.subjects(RDF.type, OWL.ObjectProperty)) +
        list(graph.subjects(RDF.type, OWL.DatatypeProperty))
    ):
        if isinstance(prop_uri, URIRef):
            # Get label if available
            label = None
            for label_obj in graph.objects(prop_uri, RDFS.label):
                label = str(label_obj)
                break
                
            properties.append({
                'uri': prop_uri,
                'label': label
            })
    
    return properties

def get_rdf_instances(graph, class_uri):
    """
    Get all instances of a specific class
    
    Args:
        graph (Graph): RDFLib Graph
        class_uri (str): URI of the class
        
    Returns:
        list: List of instance data
    """
    class_uri_ref = URIRef(class_uri)
    instances = []
    
    # Get all instances of the class
    for instance in graph.subjects(RDF.type, class_uri_ref):
        # Get all triples about this instance
        for s, p, o in graph.triples((instance, None, None)):
            instances.append([str(s), str(p), str(o)])
    
    return instances
