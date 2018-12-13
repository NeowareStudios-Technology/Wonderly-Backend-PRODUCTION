#Project: Wonderly backend
#Created by: David Ramirez
#Date: 10/16/18
#Copyright 2018 LeapWithAlice,LLC. All rights reserved

import httplib
import endpoints
from protorpc import messages
from protorpc import message_types
from google.appengine.ext import ndb

#Resource container models are used to get url query strings from HTTP requests sent to the API

##################################################################################
##################         PROTORPC MESSAGE MODELS          ######################
##################################################################################

class EmptyResponse(messages.Message):
    nothing = messages.IntegerField(1)

class EmailCheckResponse(messages.Message):
    exists = messages.StringField(1)

class ExperienceCodeResponse(messages.Message):
    code = messages.StringField(1)

class OwnedCodesResponse(messages.Message):
    titles = messages.StringField(1,repeated=True)
    codes = messages.StringField(2,repeated=True)
    dates = messages.StringField(3, repeated=True)
    coverImages = messages.StringField(4, repeated=True)

class ProfileInfoResponse(messages.Message):
    firstName = messages.StringField(1)
    lastName = messages.StringField(2)
    email = messages.StringField(3)
    createdExp = messages.IntegerField(4)

    


##################################################################################
###############      RESOURCE CONTAINER (REQUESTS) MODELS         ################
##################################################################################

EMPTY_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage
)

EMAIL_CHECK_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    email=messages.StringField(1)
)


NEW_PROF_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    firstName=messages.StringField(1),
    lastName=messages.StringField(2)

)

EDIT_PROF_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    firstName=messages.StringField(1),
    lastName=messages.StringField(2)

)

SAVE_EXP_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    title=messages.StringField(1),
    video=messages.IntegerField(2),
    model=messages.IntegerField(3),
    image=messages.IntegerField(4),
    t1=messages.BooleanField(5),
    t2=messages.BooleanField(6),
    t3=messages.BooleanField(7),
    t4=messages.BooleanField(8),
    t5=messages.BooleanField(9),
    coverImage=messages.StringField(10)
)

DEL_EXP_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    code=messages.StringField(1)
)

EDIT_EXP_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    title=messages.StringField(1),
    video=messages.IntegerField(2),
    model=messages.IntegerField(3),
    image=messages.IntegerField(4),
    code=messages.StringField(5),
    coverImage=messages.StringField(6)
)


##################################################################################
##################           DATASTORE MODELS               ######################
##################################################################################

#Profile related models------------------------------------------------------------

#EXPERIENCE CODE IS THE KEY FOR THIS DATA MODEL
class Experience(ndb.Model):
    '''Experience data model'''
    code = ndb.StringProperty(required = True)
    title = ndb.StringProperty()
    #email of the owner (email is key to profile data model)
    owner = ndb.StringProperty(required=True)
    #last time experience was edited
    edit_date = ndb.DateTimeProperty(required=True)
    video = ndb.IntegerProperty(required=True, default=False)
    model = ndb.IntegerProperty(required=True, default=False)
    image = ndb.IntegerProperty(required=True, default=False)
    cover_image = ndb.StringProperty()
    
class Profile(ndb.Model):
    '''Profile data model'''
    #email of user (key for this data model)
    email = ndb.StringProperty(required=True)
    first_name = ndb.StringProperty(required=True)
    last_name = ndb.StringProperty(required=True)
    #array of codes representing experiences created by this user
    experiences = ndb.StringProperty(repeated=True)








