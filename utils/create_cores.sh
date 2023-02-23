
APPS="drink food photos priv rx sms text wgt workout"
if [ ${ACA_ENV:-notset} == notset ]
then
    echo 'ACA_ENV not set'
    exit 1
fi

if [ ${RESOURCE_GROUP:-notset} == notset ]
then
    echo 'ACA_ENV not set'
    exit 1
fi

for APP_NAME in $APPS
do
    echo "delete container app: $APP_NAME"
    az containerapp delete --name $APP_NAME --resource-group $RESOURCE_GROUP
    
    echo "create container app: $APP_NAME"
    az containerapp create --name $APP_NAME --environment $ACA_ENV \
        --resource-group $RESOURCE_GROUP --image docker.io/solr:latest \
        --ingress external --target-port 8983 \
        --env-vars SOLR_OPTS="-Dsolr.solr.home=/share/solr/${APP_NAME}_core -Dsolr.jetty.request.header.size=65535"

    echo "extract container app: $APP_NAME"
    az containerapp show -n $APP_NAME -g $RESOURCE_GROUP -o yaml > ${APP_NAME}_0.yaml
    
    echo "modify container app: $APP_NAME"
    cat ${APP_NAME}_0.yaml | python sedit.py > ${APP_NAME}_1.yaml
    
    echo "update container app: $APP_NAME"
    az containerapp update --name $APP_NAME --resource-group $RESOURCE_GROUP  --yaml ${APP_NAME}_1.yaml
done
