
if [[ ${1}x == x ]]
then
    echo "error: need to specify service"
    echo "usage:  $0 <service>"
    exit -1
fi

cd $LTL
SERVICE=$1   
if [[ ! -d services/${SERVICE} ]]
then
    echo "error:  $SERVICE is not a valid service"
    exit -1
fi

echo ORCH_TESTING_MODE=1 FLASK_ENV=development PYTHONPATH=. python services/${SERVICE}/appfactory.py
ORCH_TESTING_MODE=1 FLASK_ENV=development PYTHONPATH=. python services/${SERVICE}/appfactory.py

