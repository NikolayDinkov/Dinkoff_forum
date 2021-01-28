# Dinkoff_forum
# install
virtualenv env

source env/bin/activate

pip install -r requirements.txt

# run
export FLASK_ENV=development

flask run
