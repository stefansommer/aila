# aula.py
#
# This interface to Aula is written by Morten Helmstedt. E-mail: helmstedt@gmail.com see https://helmstedt.dk/2021/05/aulas-api-en-opdatering/
#
''' An example of how to log in to the Danish LMS Aula (https://aula.dk) and
extract data from the API. Could be further developed to also submit data and/or to
create your own web or terminal interface(s) for Aula.'''

# Imports
import requests                 # Perform http/https requests
from bs4 import BeautifulSoup   # Parse HTML pages
import json                     # Needed to print JSON API data

# Load the user information from the JSON file
with open('userinfo.json', 'r') as file:
    user = json.load(file)

def run():
    # Start requests session
    session = requests.Session()

    # Get login page
    url = 'https://www.aula.dk/auth/login.php?type=unilogin'
    response = session.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    post_url = soup.form['action']
    params = {
        'selectedIdp': 'uni_idp'
    }

    # Get login form
    response = session.post(post_url, data=params)

    # Login is handled by a loop where each page is first parsed by BeautifulSoup.
    # Then the destination of the form is saved as the next url to post to and all
    # inputs are collected with special cases for the username and password input.
    # Once the loop reaches the Aula front page the loop is exited. The loop has a
    # maximum number of iterations to avoid an infinite loop if something changes
    # with the Aula login.
    counter = 0
    success = False
    while success == False and counter < 10:
        try:
            # Parse response using BeautifulSoup
            soup = BeautifulSoup(response.text, "lxml")
            # Get destination of form element (assumes only one)
            url = soup.form['action']   

            # If form has a destination, inputs are collected and names and values
            # for posting to form destination are saved to a dictionary called data
            if url:
                # Get all inputs from page
                inputs = soup.find_all('input')
                # Check whether page has inputs
                if inputs:
                    # Create empty dictionary 
                    data = {}
                    # Loop through inputs
                    for input in inputs:
                        # Some inputs may have no names or values so a try/except
                        # construction is used.
                        try:
                            # Login takes place in single input steps, which
                            # is the reason for the if/elif construction
                            # Save username if input is a username field
                            if input['name'] == 'username':
                                data[input['name']] = user['username']
                            # Save password if input is a password field
                            elif input['name'] == 'password':
                                data[input['name']] = user['password']
                            # The login procedure has an additional field to select a role
                            # If an employee needs to login, this value needs to be changed
                            elif input['name'] == 'selected-aktoer':
                                data[input['name']] = "KONTAKT"
                                #data[input['name']] = "MEDARBEJDER_EKSTERN"    # Replace above line with this for employees
                            # For all other inputs, save name and value of input
                            else:
                                data[input['name']] = input['value']
                        # If input has no value, an error is caught but needs no handling
                        # since inputs without values do not need to be posted to next
                        # destination.
                        except:
                            pass
                # If there's data in the dictionary, it is submitted to the destination url
                if data:
                    response = session.post(url, data=data)
                # If there's no data, just try to post to the destination without data
                else:
                    response = session.post(url)
                # If the url of the response is the Aula front page, loop is exited
                if response.url == 'https://www.aula.dk:443/portal/':
                    success = True
        # If some error occurs, try to just ignore it
        except Exception as e:
            print(e)
            pass
        # One is added to counter each time the loop runs independent of outcome
        counter += 1

    # Login succeeded without an HTTP error code and API requests can begin 
    if success == True and response.status_code == 200:
        #print("Login lykkedes")

        # All API requests go to the below url
        # Each request has a number of parameters, of which method is always included
        # Data is returned in JSON
        url = 'https://www.aula.dk/api/v17/'

        ### First API request. This request must be run to generate correct correct cookies for subsequent requests. ###
        params = {
            'method': 'profiles.getProfilesByLogin'
            }
        # Perform request, convert to json and print on screen
        response_profile = session.get(url, params=params).json()
        #print(json.dumps(response_profile, indent=4))

        ### Second API request. This request must be run to generate correct correct cookies for subsequent requests. ###
        params = {
            'method': 'profiles.getProfileContext',
            'portalrole': 'guardian',   # 'guardian' for parents (or other guardians), 'employee' for employees
        }
        # Perform request, convert to json and print on screen
        response_profile_context = session.get(url, params=params).json()
        #print(json.dumps(response_profile_context, indent=4))

        # Loop to get institutions and children associated with profile and save
        # them to lists
        institutions = []
        institution_profiles = []
        children = []
        for institution in response_profile_context['data']['institutions']:
            institutions.append(institution['institutionCode'])
            institution_profiles.append(institution['institutionProfileId'])
            for child in institution['children']:
                children.append(child['id'])

        children_and_institution_profiles = institution_profiles + children

        ### Third example API request, uses data collected from second request ###
        params = {
            'method': 'notifications.getNotificationsForActiveProfile',
            'activeChildrenIds[]': children,
            'activeInstitutionCodes[]': institutions
        }

        # Perform request, convert to json and print on screen
        notifications = session.get(url, params=params).json()
        #print(json.dumps(notifications, indent=4))

        ### Fourth example API request, only succeeds when the third has been run before ###
        params = {
            'method': 'messaging.getThreads',
            'sortOn': 'date',
            'orderDirection': 'desc',
            'page': '0'
        }

        # Perform request, convert to json and print on screen
        messages = session.get(url, params=params).json()
        #print(json.dumps(messages, indent=4))

        ### Fifth example. getAllPosts uses a combination of children and instituion profiles. ###
        params = {
            'method': 'posts.getAllPosts',
            'parent': 'profile',
            'index': "0",
            'institutionProfileIds[]': children_and_institution_profiles,
            'limit': '2'
        }

        # Perform request, convert to json and print on screen
        posts = session.get(url, params=params).json()
        #print(json.dumps(posts, indent=4))

        return posts,messages

    # Login failed for some unknown reason
    else:
        raise Exception("Noget gik galt med login")
