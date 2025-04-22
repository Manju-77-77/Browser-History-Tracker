# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from stack import Stack

app = Flask(__name__)
app.secret_key = 'browser_simulation_secret_key'

@app.route('/')
def index():
    # Initialize session data if not exists
    if 'tabs' not in session:
        session['tabs'] = [{'id': 1, 'title': 'New Tab', 'url': '', 'history': [], 'forward': []}]
        session['active_tab'] = 1
        session['next_tab_id'] = 2
    
    return render_template('index.html', 
                          tabs=session['tabs'], 
                          active_tab=session['active_tab'])

@app.route('/visit', methods=['POST'])
def visit():
    data = request.get_json()
    url = data.get('url', '').strip()
    tab_id = int(data.get('tabId', session['active_tab']))
    
    if url:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
            
        # Find the active tab
        for tab in session['tabs']:
            if tab['id'] == tab_id:
                # Add current URL to history if it exists
                if tab['url']:
                    tab['history'].append(tab['url'])
                
                # Clear forward stack when visiting new URL
                tab['forward'] = []
                
                # Set new URL and update title
                tab['url'] = url
                tab['title'] = get_title_from_url(url)
                break
                
        session.modified = True
        return jsonify({'url': url, 'title': get_title_from_url(url)})
    
    return jsonify({'url': None})

@app.route('/back', methods=['POST'])
def go_back():
    data = request.get_json()
    tab_id = int(data.get('tabId', session['active_tab']))
    
    for tab in session['tabs']:
        if tab['id'] == tab_id and tab['history']:
            # Move current URL to forward stack
            tab['forward'].append(tab['url'])
            
            # Set URL to last history item
            tab['url'] = tab['history'].pop()
            tab['title'] = get_title_from_url(tab['url'])
            
            session.modified = True
            return jsonify({'url': tab['url'], 'title': tab['title']})
    
    return jsonify({'url': None})

@app.route('/forward', methods=['POST'])
def go_forward():
    data = request.get_json()
    tab_id = int(data.get('tabId', session['active_tab']))
    
    for tab in session['tabs']:
        if tab['id'] == tab_id and tab['forward']:
            # Move current URL to history
            if tab['url']:
                tab['history'].append(tab['url'])
            
            # Set URL to next forward item
            tab['url'] = tab['forward'].pop()
            tab['title'] = get_title_from_url(tab['url'])
            
            session.modified = True
            return jsonify({'url': tab['url'], 'title': tab['title']})
    
    return jsonify({'url': None})

@app.route('/newtab', methods=['POST'])
def new_tab():
    # Create a new tab
    new_tab_id = session.get('next_tab_id', len(session['tabs']) + 1)
    session['tabs'].append({
        'id': new_tab_id,
        'title': 'New Tab',
        'url': '',
        'history': [],
        'forward': []
    })
    session['active_tab'] = new_tab_id
    session['next_tab_id'] = new_tab_id + 1
    session.modified = True
    
    return jsonify({'tabId': new_tab_id})

@app.route('/switchtab/<int:tab_id>', methods=['POST'])
def switch_tab(tab_id):
    session['active_tab'] = tab_id
    session.modified = True
    
    # Find the tab data
    tab_data = None
    for tab in session['tabs']:
        if tab['id'] == tab_id:
            tab_data = tab
            break
    
    if tab_data:
        return jsonify({
            'url': tab_data.get('url', ''),
            'title': tab_data.get('title', 'New Tab')
        })
    return jsonify({'url': '', 'title': 'New Tab'})

@app.route('/closetab/<int:tab_id>', methods=['POST'])
def close_tab(tab_id):
    # Find and remove the tab
    for i, tab in enumerate(session['tabs']):
        if tab['id'] == tab_id:
            session['tabs'].pop(i)
            break
    
    # If we closed the active tab, activate another tab
    if session['active_tab'] == tab_id:
        if session['tabs']:
            session['active_tab'] = session['tabs'][0]['id']
        else:
            # If no tabs left, create a new one
            new_tab_id = session.get('next_tab_id', 1)
            session['tabs'] = [{
                'id': new_tab_id,
                'title': 'New Tab',
                'url': '',
                'history': [],
                'forward': []
            }]
            session['active_tab'] = new_tab_id
            session['next_tab_id'] = new_tab_id + 1
    
    session.modified = True
    return jsonify({'activeTabId': session['active_tab']})

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data.get('query', '').strip()
    tab_id = int(data.get('tabId', session['active_tab']))
    
    if query:
        # Check if it's a URL or a search query
        if ('.' in query and ' ' not in query) or query.startswith('http'):
            if not query.startswith('http'):
                query = 'https://' + query
            search_url = query
        else:
            # Use Google search API
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            
        # Update the tab with the search URL
        for tab in session['tabs']:
            if tab['id'] == tab_id:
                if tab['url']:
                    tab['history'].append(tab['url'])
                tab['url'] = search_url
                tab['title'] = f"Search: {query}" if 'google.com/search' in search_url else query
                tab['forward'] = []
                break
                
        session.modified = True
        return jsonify({'url': search_url, 'title': f"Search: {query}" if 'google.com/search' in search_url else query})
    
    return jsonify({'url': None})

@app.route('/clear_history', methods=['POST'])
def clear_history():
    data = request.get_json()
    tab_id = int(data.get('tabId', session['active_tab']))
    
    for tab in session['tabs']:
        if tab['id'] == tab_id:
            tab['history'] = []
            tab['forward'] = []
            break
    
    session.modified = True
    return jsonify({'success': True})

@app.route('/clear_all_history', methods=['POST'])
def clear_all_history():
    for tab in session['tabs']:
        tab['history'] = []
        tab['forward'] = []
    
    session.modified = True
    return jsonify({'success': True})

def get_title_from_url(url):
    """Extract a simple title from URL for display purposes"""
    if not url:
        return "New Tab"
    
    # Remove protocol
    if '://' in url:
        domain = url.split('://', 1)[1]
    else:
        domain = url
    
    # Remove path
    if '/' in domain:
        domain = domain.split('/', 1)[0]
    
    # Remove www.
    if domain.startswith('www.'):
        domain = domain[4:]
    
    return domain

if __name__ == '__main__':
    app.run(debug=True)