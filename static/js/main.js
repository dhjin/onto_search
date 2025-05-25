document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize DataTables for results table if it exists
    if (document.getElementById('resultsTable')) {
        $('#resultsTable').DataTable({
            responsive: true,
            pageLength: 25,
            language: {
                search: "Filter results:",
                lengthMenu: "Show _MENU_ entries per page",
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
                infoEmpty: "Showing 0 to 0 of 0 entries",
                infoFiltered: "(filtered from _MAX_ total entries)"
            }
        });
    }

    // Query suggestion functionality
    const suggestQueriesBtn = document.getElementById('suggestQueries');
    const queryTextArea = document.getElementById('queryTextArea');
    const suggestionsList = document.getElementById('suggestionsList');
    
    if (suggestQueriesBtn) {
        suggestQueriesBtn.addEventListener('click', function() {
            // Show loading spinner
            suggestQueriesBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
            suggestQueriesBtn.disabled = true;
            
            // Fetch suggested queries from the API
            fetch('/api/suggest_queries')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    // Clear existing suggestions
                    suggestionsList.innerHTML = '';
                    
                    // Add new suggestions
                    data.forEach(suggestion => {
                        const listItem = document.createElement('li');
                        listItem.className = 'list-group-item list-group-item-action';
                        listItem.innerHTML = `<strong>${suggestion.name}</strong>`;
                        listItem.addEventListener('click', function() {
                            queryTextArea.value = suggestion.query.trim();
                            // Close the suggestions dropdown
                            const suggestionModal = bootstrap.Modal.getInstance(document.getElementById('suggestionsModal'));
                            if (suggestionModal) {
                                suggestionModal.hide();
                            }
                        });
                        suggestionsList.appendChild(listItem);
                    });
                    
                    // Show the suggestions modal
                    const suggestionsModal = new bootstrap.Modal(document.getElementById('suggestionsModal'));
                    suggestionsModal.show();
                })
                .catch(error => {
                    console.error('Error fetching suggestions:', error);
                    alert('Error loading query suggestions. Please try again.');
                })
                .finally(() => {
                    // Reset button state
                    suggestQueriesBtn.innerHTML = 'Suggest Queries';
                    suggestQueriesBtn.disabled = false;
                });
        });
    }

    // Handle tab functionality for ontology explorer
    const ontologyTabs = document.querySelectorAll('button[data-bs-toggle="tab"]');
    ontologyTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Remove active class from all tabs
            ontologyTabs.forEach(t => t.classList.remove('active'));
            // Add active class to clicked tab
            this.classList.add('active');
        });
    });

    // Copy example query to the query textarea
    const exampleQueryBtns = document.querySelectorAll('.copy-example');
    exampleQueryBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const query = this.getAttribute('data-query');
            if (queryTextArea && query) {
                queryTextArea.value = query;
                queryTextArea.focus();
                
                // Scroll to query form
                document.getElementById('queryForm').scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

// Function to copy results to clipboard
function copyResults() {
    const resultsTable = document.getElementById('resultsTable');
    if (!resultsTable) return;
    
    // Get table data
    const table = $('#resultsTable').DataTable();
    let csvContent = "";
    
    // Add headers
    const headers = [];
    resultsTable.querySelectorAll('thead th').forEach(th => {
        headers.push(th.textContent);
    });
    csvContent += headers.join(',') + '\n';
    
    // Add data rows
    table.data().each(function(rowData) {
        const values = rowData.map(value => {
            // Escape commas and quotes
            if (typeof value === 'string') {
                value = value.replace(/"/g, '""');
                if (value.includes(',') || value.includes('"') || value.includes('\n')) {
                    value = `"${value}"`;
                }
            }
            return value;
        });
        csvContent += values.join(',') + '\n';
    });
    
    // Create a temporary textarea element to copy the CSV content
    const textarea = document.createElement('textarea');
    textarea.value = csvContent;
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
        document.execCommand('copy');
        const toastEl = document.getElementById('copyToast');
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    } catch (err) {
        console.error('Failed to copy results: ', err);
        alert('Failed to copy results to clipboard');
    } finally {
        document.body.removeChild(textarea);
    }
}

// Function to export results as CSV
function exportResults() {
    const resultsTable = document.getElementById('resultsTable');
    if (!resultsTable) return;
    
    // Get table data
    const table = $('#resultsTable').DataTable();
    let csvContent = "data:text/csv;charset=utf-8,";
    
    // Add headers
    const headers = [];
    resultsTable.querySelectorAll('thead th').forEach(th => {
        headers.push(th.textContent);
    });
    csvContent += headers.join(',') + '\n';
    
    // Add data rows
    table.data().each(function(rowData) {
        const values = rowData.map(value => {
            // Escape commas and quotes
            if (typeof value === 'string') {
                value = value.replace(/"/g, '""');
                if (value.includes(',') || value.includes('"') || value.includes('\n')) {
                    value = `"${value}"`;
                }
            }
            return value;
        });
        csvContent += values.join(',') + '\n';
    });
    
    // Create download link
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'ontology_query_results.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Function to toggle between showing and hiding sample queries
function toggleSampleQueries() {
    const sampleQueries = document.getElementById('sampleQueries');
    const toggleBtn = document.getElementById('toggleSampleQueriesBtn');
    
    if (sampleQueries.style.display === 'none') {
        sampleQueries.style.display = 'block';
        toggleBtn.textContent = 'Hide Sample Queries';
    } else {
        sampleQueries.style.display = 'none';
        toggleBtn.textContent = 'Show Sample Queries';
    }
}
