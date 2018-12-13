#Project: Wonderly backend
#Created by: David Ramirez
#Date: 10/17/18
#Copyright 2018 LeapWithAlice,LLC. All rights reserved

#for sending HTML requests to auth0------------------------------------------
import urllib2
import urllib
import json
import random
import string
#----------------------------------------------------------------------------
#only radians from math
from math import radians
from cmath import sqrt, asin, cos, sin

from datetime import datetime
from datetime import timedelta

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from models import Experience
from models import Profile

from models import EMPTY_REQUEST
from models import SAVE_EXP_REQUEST
from models import NEW_PROF_REQUEST
from models import DEL_EXP_REQUEST
from models import EDIT_EXP_REQUEST
from models import EDIT_PROF_REQUEST
from models import EMAIL_CHECK_REQUEST

from models import EmptyResponse
from models import ExperienceCodeResponse
from models import OwnedCodesResponse
from models import ProfileInfoResponse
from models import EmailCheckResponse


#firebase client ID 
FIREBASE_ID = "582959696093-6emps5ivjnc1andqinlue7s1nj0bkabv.apps.googleusercontent.com"


##################################################################################
##################            ENDPOINTS DECLARAION          ######################
##################################################################################

@endpoints.api(
    name='wonderly',
    version='v1',
    allowed_client_ids=[FIREBASE_ID],
    issuers={'firebase': endpoints.Issuer(
        'https://securetoken.google.com/wonderly-225214',
        'https://www.googleapis.com/service_accounts/v1/metadata/x509/securetoken@system.gserviceaccount.com')})
class wonderlyApi(remote.Service):
  """wonderly API v1."""


##################################################################################
##################            HELPER FUNCTIONS              ######################
##################################################################################
  
  #***HELPER FUNCTION: AUTHENTICATE USER***
  #Description: make sure that user has an account. if the user does not have an account, raise exception. 
  #Params: endpoints user object
  #Returns: none
  #Called by: any endpoint
  def _authenticateUser(self):
    user = endpoints.get_current_user()
    if not user:
      raise endpoints.UnauthorizedException('Authorization required')
    return user

  #***HELPER FUNCTION: SAVE NEW EXPERIENCE***
  #Description: creates experience code and saves experience in db
  #Params: SAVE_EXP_REQUEST
  #Returns: ExperienceCodeResponse
  #Called by: SaveNewExperience
  def _saveNewExperience(self, request, user):
    profile = ndb.Key(Profile, user.email()).get()
    #this will hold the 6 character lower case code
    code = ''
    n = 6
    #create parent key from users email
    parent_key = ndb.Key(Profile, user.email())
    #create the 6 character experience code from lower case letters
    code = ''.join(random.choice(string.ascii_lowercase) for _ in range(n))
    code_query = Experience.query(Experience.code == code)
    existing_experience = code_query.get()
    #while experience code already exists in db, recreate code until it doesnt match any existing codes
    while existing_experience:
      code = ''.join(random.choice(string.ascii_lowercase) for _ in range(n))
      code_query = Experience.query(Experience.code == code)
      existing_experience = code_query.get()
    #create instance of experience data model to save in db
    profile.experiences.append(code)
    new_experience = Experience(
      parent = parent_key,
      code = code,
      owner = user.email(),
      title = getattr(request, 'title'),
      edit_date = datetime.now(),
      video = getattr(request, 'video'),
      model = getattr(request, 'model'),
      image = getattr(request, 'image'),
      cover_image = getattr(request, 'coverImage')
    )
    #save new experience
    new_experience.put()
    profile.put()
    #return code
    response = ExperienceCodeResponse(
      code = code
    )
    return response


  #***HELPER FUNCTION: EDIT EXPERIENCE***
  #Description: edits existing experience in db
  #Params: EDIT_EXP_REQUEST
  #Returns: None
  #Called by: EditExperience
  def _editExperience(self, request, user):
    #make sure user has profile
    profile = ndb.Key(Profile, user.email()).get()
    if not profile:
      raise endpoints.BadRequestException('profile does not exist')
    #this will hold the 6 character lower case code
    code = getattr(request,"code")
    #get the experience
    experience_query = Experience.query(ancestor=profile.key)
    experience_query2 = experience_query.filter(Experience.code ==code)
    experienceToEdit = experience_query2.get()
    #make sure experience exists
    if not experienceToEdit:
      raise endpoints.BadRequestException('experience does not exist')
    #make edits
    experienceToEdit.title = getattr(request,"title")
    experienceToEdit.edit_date = datetime.now()
    experienceToEdit.video = getattr(request,"video")
    experienceToEdit.model = getattr(request,"model")
    experienceToEdit.image = getattr(request,"image")
    experienceToEdit.cover_image = getattr(request, "coverImage")
    experienceToEdit.put()
  
    return EmptyResponse()

  #***HELPER FUNCTION: DELETE EXPERIENCE***
  #Description: deletes the experience from the db
  #Params: DEL_EXP_REQUEST
  #Returns: none
  #Called by: DeleteExperience
  def _deleteExperience(self, request, user):
    p_key = ndb.Key(Profile, user.email())
    profile = p_key.get()
    #if profile already exists, raise exception
    if not profile:
      raise endpoints.BadRequestException('profile does not exist')
    #else, get AR experience (Journey)
    experience_query = Experience.query(ancestor=p_key)
    experience_query2 = experience_query.filter(Experience.code ==getattr(request, "code"))
    experience = experience_query2.get()
    #raise exception if experience (Journey) not found
    if not experience:
      raise endpoints.BadRequestException('experience does not exist')
    #delete experience (journey)
    experience.key.delete()
    #delete the record of the experience (journey) from the users profile
    profile.experiences.remove(getattr(request, "code"))

    return EmptyResponse()

  #***HELPER FUNCTION: CREATE NEW PROFILE***
  #Description: creates new profile and stores in db
  #Params: NEW_PROF_REQUEST
  #Returns: none
  #Called by: NewProfile
  def _newProfile(self, request, user):
    p_key = ndb.Key(Profile, user.email())
    profile = p_key.get()
    #if profile already exists, raise exception
    if profile:
      raise endpoints.BadRequestException('email already in use')
    #else
    profile = Profile(
      key= p_key,
      email = user.email(),
      first_name = getattr(request, 'firstName'),
      last_name = getattr(request, 'lastName')
    )
    profile.put()

    return EmptyResponse()

  #***HELPER FUNCTION: EDIT PROFILE***
  #Description: edits profile first or last name in google datastore
  #Params: NEW_PROF_REQUEST
  #Returns: none
  #Called by: EditProfile
  def _editProfile(self, request, user):
    p_key = ndb.Key(Profile, user.email())
    profile = p_key.get()
    #if profile already exists, raise exception
    if not profile:
      raise endpoints.BadRequestException('profile not found')
    #else

    #if the user has supplied a first name, change it to the supplied name
    if (getattr(request, "firstName") != ""):
      profile.first_name = getattr(request, "firstName")

    #if the user has supplied a last name, change it to the supplied name
    if (getattr(request, "lastName") !=""):
      profile.last_name = getattr(request, "lastName")

    #save profile
    profile.put()

    return EmptyResponse()

  #***HELPER FUNCTION: GET ALL CODES OWNED BY USER***
  #Description: returns codes of all experiences (up to 50) owned by the user ordered by most recently edited
  #Params: none
  #Returns: ownedCodesResponse
  #Called by: GetOwnedCodes endpoint
  def _getOwnedCodes(self, request, user):
    #get user profile
    profile_key = ndb.Key(Profile, user.email())

    #get all (up to 50) of the user's created experiences
    all_owned_experiences = Experience.query(ancestor=profile_key).fetch(50)

    #declare tracker lists to keep track of dates, titles, codes, indexes, and cover images (for sorting)
    date_tracker_list = []
    title_tracker_list = []
    code_tracker_list = []
    cover_image_tracker_list = []
    index_tracker = []

    #set tracker lists 
    for experience in all_owned_experiences:
      code_tracker_list.append(experience.code)
      title_tracker_list.append(experience.title)
      date_tracker_list.append(experience.edit_date)
      cover_image_tracker_list.append(experience.cover_image)

    
    #set index tracker to have as many elements as indexes e.g. [0, 1, 2, 3, 4, 5, 6, 7]
    for x in range(0,len(all_owned_experiences)):
      index_tracker.append(x)

    #zip index tracker and date tracker lists into a dict (index = key, date = value)
    date_sorter_dict = dict(zip(index_tracker, date_tracker_list))

    #declare lists to hold sorted codes, indices, dates, and titles
    sorted_codes_list = []
    sorted_index_list = []
    sorted_date_list = []
    sorted_titles_list = []
    sorted_cover_images_list = []

    #sort the index/date dictionary by date and save sorted values to sorted lists
    for key, value in sorted(date_sorter_dict.iteritems(), key=lambda (k,v): (v,k), reverse=True):
      sorted_index_list.append(key)
      sorted_date_list.append(value)
    
    #use the indices of the sorted index list to also sort codes, titles, and images
    for index in sorted_index_list:
      sorted_codes_list.append(code_tracker_list[index]) 
      sorted_titles_list.append(title_tracker_list[index])
      sorted_cover_images_list.append(cover_image_tracker_list[index])

    #all codes, titles, date, and cover image "sorted lists" are now properly indexed to each other and sorted by most recent edit date of experience

    #create and set response
    response = OwnedCodesResponse()
    response.codes = sorted_codes_list
    response.titles = sorted_titles_list
    response.coverImages = sorted_cover_images_list
    #convert datetime object to easier to read format
    for date in sorted_date_list:
      response.dates.append(date.strftime('%m-%d-%Y'))
    
    return response

  #***HELPER FUNCTION: GET USER PROFILE INFO***
  #Description: returns first name, last name, number of created experiences
  #Params: none
  #Returns: ProfileInfoResponse
  #Called by: GetProfileInfo
  def _getProfileInfo(self, request, user):
    profile = ndb.Key(Profile, user.email()).get()
    if not profile:
      raise endpoints.BadRequestException("user does not have a profile")
    
    response = ProfileInfoResponse(
      firstName = profile.first_name,
      lastName = profile.last_name,
      email = user.email(),
      createdExp = len(profile.experiences)
    )
    
    return response
  
  #***HELPER FUNCTION: CEHCK IF EMAIL EXISTS***
  #Description: takes email and checks if a user is already using that email
  #Params: email
  #Returns: CheckEmailResponse
  #Called by: EmailCheck
  def _emailCheck(self, request):
    profile = ndb.Key(Profile, getattr(request, "email")).get()
    response = EmailCheckResponse(
      exists = "y"
    )

    if not profile:
      response.exists = "n"
    
    return response



##################################################################################
##################           ENDPOINT FUNCTIONS             ######################
##################################################################################

  #****ENDPOINT: Saves new experience in db as child of profile entity and returns unique exp code***
  #-accepts: experience info
  #-returns: 5 character (lower case) exp code
  @endpoints.method(SAVE_EXP_REQUEST, ExperienceCodeResponse, 
  path='exp', http_method='PUT', name='SaveNewExperience')
  def SaveNewExperience(self, request):
    user = self._authenticateUser()
    return self._saveNewExperience(request, user)

  #****ENDPOINT: Deletes Experience (user must be owner)***
  #-accepts: 5 character lower case exp code
  #-returns: none
  @endpoints.method(DEL_EXP_REQUEST, EmptyResponse, 
  path='exp/delete', http_method='PUT', name='DeleteExperience')
  def DeleteExperience(self, request):
    user = self._authenticateUser()
    return self._deleteExperience(request, user)

  #****ENDPOINT: Edits Experience (user must be owner)***
  #-accepts: experience info
  #-returns: none
  @endpoints.method(EDIT_EXP_REQUEST, EmptyResponse, 
  path='exp/edit', http_method='PUT', name='EditExperience')
  def EditExperience(self, request):
    user = self._authenticateUser()
    return self._editExperience(request, user)

  #****ENDPOINT: Creates new user profile***
  #-accepts: first name, last name
  #-returns: none
  @endpoints.method(NEW_PROF_REQUEST, EmptyResponse, 
  path='profile', http_method='PUT', name='NewProfile')
  def NewProfile(self, request):
    user = self._authenticateUser()
    return self._newProfile(request, user)

  #****ENDPOINT: Edits user profile***
  #-accepts: (possible)first name, last name 
  #-returns: none
  @endpoints.method(EDIT_PROF_REQUEST, EmptyResponse, 
  path='profile/edit', http_method='PUT', name='EditProfile')
  def EditProfile(self, request):
    user = self._authenticateUser()
    return self._editProfile(request, user)

  #****ENDPOINT: Returns all created experience codes***
  #-accepts: none
  #-returns: array of all experience codes (up to 50)
  @endpoints.method(EMPTY_REQUEST, OwnedCodesResponse, 
  path='profile/codes', http_method='GET', name='GetOwnedCodes')
  def GetOwnedCodes(self, request):
    user = self._authenticateUser()
    return self._getOwnedCodes(request, user)

  #****ENDPOINT: Returns profile info***
  #-accepts: none
  #-returns: user first name, last name,, email, number of created experiences
  @endpoints.method(EMPTY_REQUEST, ProfileInfoResponse, 
  path='profile', http_method='GET', name='GetProfileInfo')
  def GetProfileInfo(self, request):
    user = self._authenticateUser()
    return self._getProfileInfo(request, user)

  #****ENDPOINT: Returns whether an email is already taken***
  #-accepts: email
  #-returns: exists (bool)
  @endpoints.method(EMAIL_CHECK_REQUEST, EmailCheckResponse, 
  path='profile/check', http_method='PUT', name='EmailCheck')
  def EmailCheck(self, request):
    return self._emailCheck(request)
 
  
api = endpoints.api_server([wonderlyApi])