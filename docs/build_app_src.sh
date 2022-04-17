#!/bin/bash

# This script produces the .rst files for each SciPost app.
# These files are then ingested by sphinx's make html command.

# current directory is docs

cd codebase/apps

apps_basedir='../../../../scipost_django'

# Traverse the different app types one by one

cd core

# NOTE: do NOT run sphinx-apidoc on app SciPost_v1 like for the other apps below,
# since SciPost_v1.settings.base.py must not be imported, potentially revealing
# the contents of secrets.json for the system on which sphinx-apidoc is run).
rm -rf SciPost_v1/*
sphinx-apidoc --separate -o SciPost_v1 $apps_basedir/SciPost_v1 $apps_basedir/SciPost_v1/settings $apps_basedir/SciPost_v1/wsgi_*


for app in scipost common # SciPost_v1 must NOT be on this list (see above)
do
    rm -rf $app/*
    sphinx-apidoc --separate -o $app/ $apps_basedir/$app $apps_basedir/$app/migrations
done

cd ../people

for app in colleges conflicts profiles
do
    rm -rf $app/*
    sphinx-apidoc --separate -o $app/ $apps_basedir/$app $apps_basedir/$app/migrations
done

cd ../preprints

for app in preprints
do
    rm -rf $app/*
    sphinx-apidoc --separate -o $app/ $apps_basedir/$app $apps_basedir/$app/migrations
done

cd ../editorial

for app in submissions
do
    rm -rf $app/*
    sphinx-apidoc --separate -o $app/ $apps_basedir/$app $apps_basedir/$app/migrations
done

cd ../publishing

for app in journals proceedings series
do
    rm -rf $app/*
    sphinx-apidoc --separate -o $app/ $apps_basedir/$app $apps_basedir/$app/migrations
done

cd ../publishing_other

for app in commentaries comments theses
do
    rm -rf $app/*
    sphinx-apidoc --separate -o $app/ $apps_basedir/$app $apps_basedir/$app/migrations
done

cd ../metadata

for app in funders ontology organizations
do
    rm -rf $app/*
    sphinx-apidoc --separate -o $app/ $apps_basedir/$app $apps_basedir/$app/migrations
done

cd ../production

for app in production
do
    rm -rf $app/*
    sphinx-apidoc --separate -o $app/ $apps_basedir/$app $apps_basedir/$app/migrations
done

cd ../business

for app in careers finances sponsors
do
    rm -rf $app/*
    sphinx-apidoc --separate -o $app/ $apps_basedir/$app $apps_basedir/$app/migrations
done

cd ../information

for app in guides
do
    rm -rf $app/*
    sphinx-apidoc --separate -o $app/ $apps_basedir/$app $apps_basedir/$app/migrations
done

cd ../communications

for app in mailing_lists mails news notifications
do
    rm -rf $app/*
    sphinx-apidoc --separate -o $app/ $apps_basedir/$app $apps_basedir/$app/migrations
done

cd ../utilities

for app in forums helpdesk invitations markup stats
do
    rm -rf $app/*
    sphinx-apidoc --separate -o $app/ $apps_basedir/$app $apps_basedir/$app/migrations
done

cd ../../..
