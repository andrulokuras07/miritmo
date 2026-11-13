# Bitácora de despliegue – MiRitmo (Entregable 1)

Cada comando con su salida. Los secretos se omiten o aparecen como `***`.

## 1. Identidad de la sesión AWS

_2026-11-13 11:50_ · código de salida 0

```
> aws sts get-caller-identity --profile miritmo
{
    "UserId": "AROAULMOKKJQ4NMMXZO2L:94d80438-5021-70c9-8465-db1f91703d30",
    "Account": "299335570017",
    "Arn": "arn:aws:sts::299335570017:assumed-role/AccountFullAccessRole/94d80438-5021-70c9-8465-db1f91703d30"
}
```

## 2. Plan de la cuenta (Free Tier)

_2026-11-13 11:50_ · código de salida 0

```
> aws freetier get-account-plan-state --profile miritmo --region us-east-1
{
    "accountId": "299335570017",
    "accountPlanType": "FREE",
    "accountPlanStatus": "ACTIVE",
    "accountPlanRemainingCredits": {
        "amount": 100.0,
        "unit": "USD"
    },
    "accountPlanExpirationDate": "2027-05-13T14:33:30.809000+00:00"
}
```

## 3. Rol de la sesión

_2026-11-13 11:50_ · código de salida 0

```
> aws iam list-roles --profile miritmo --query Roles[?RoleName=='AccountFullAccessRole'].[RoleName,Path,Arn] --output text
AccountFullAccessRole	/managed/	arn:aws:iam::299335570017:role/managed/AccountFullAccessRole
```

## 4. Bloqueo de acceso público de S3 a nivel cuenta

_2026-11-13 11:50_ · código de salida 254

```
> aws s3control get-public-access-block --account-id 299335570017 --profile miritmo --region us-east-2
[stderr]

aws: [ERROR]: An error occurred (NoSuchPublicAccessBlockConfiguration) when calling the GetPublicAccessBlock operation: The public access block configuration was not found
```

## 5. Límites de Lambda en la cuenta

_2026-11-13 11:50_ · código de salida 0

```
> aws lambda get-account-settings --profile miritmo --region us-east-2 --query AccountLimit
{
    "TotalCodeSize": 322122547200,
    "CodeSizeUnzipped": 262144000,
    "CodeSizeZipped": 52428800,
    "ConcurrentExecutions": 400,
    "UnreservedConcurrentExecutions": 400
}
```

## 6. Simulador de políticas IAM: acciones del despliegue (sin crear recursos)

_2026-11-13 11:50_ · código de salida 0

```
> aws iam simulate-principal-policy --profile miritmo --policy-source-arn arn:aws:iam::299335570017:role/managed/AccountFullAccessRole --action-names s3:CreateBucket s3:PutBucketPublicAccessBlock s3:PutBucketPolicy s3:PutObject cloudfront:CreateOriginAccessControl cloudfront:CreateDistribution cloudfront:CreateInvalidation iam:CreateRole iam:AttachRolePolicy iam:PassRole lambda:CreateFunction lambda:CreateFunctionUrlConfig lambda:AddPermission lambda:UpdateFunctionConfiguration logs:FilterLogEvents --query EvaluationResults[].[EvalActionName,EvalDecision] --output text
s3:CreateBucket	explicitDeny
s3:PutBucketPublicAccessBlock	explicitDeny
s3:PutBucketPolicy	explicitDeny
s3:PutObject	explicitDeny
cloudfront:CreateOriginAccessControl	allowed
cloudfront:CreateDistribution	allowed
cloudfront:CreateInvalidation	allowed
iam:CreateRole	allowed
iam:AttachRolePolicy	allowed
iam:PassRole	allowed
lambda:CreateFunction	explicitDeny
lambda:CreateFunctionUrlConfig	explicitDeny
lambda:AddPermission	explicitDeny
lambda:UpdateFunctionConfiguration	explicitDeny
logs:FilterLogEvents	allowed
```

## 7. Simulador IAM con aws:RequestedRegion=us-east-2

_2026-11-13 11:50_ · código de salida 0

```
> aws iam simulate-principal-policy --profile miritmo --policy-source-arn arn:aws:iam::299335570017:role/managed/AccountFullAccessRole --action-names s3:CreateBucket s3:PutBucketPublicAccessBlock s3:PutBucketPolicy s3:PutObject lambda:CreateFunction lambda:CreateFunctionUrlConfig lambda:AddPermission lambda:UpdateFunctionConfiguration --context-entries ContextKeyName=aws:RequestedRegion,ContextKeyValues=us-east-2,ContextKeyType=string --query EvaluationResults[].[EvalActionName,EvalDecision,join(',',MatchedStatements[].SourcePolicyId)] --output text
s3:CreateBucket	allowed	AdministratorAccess
s3:PutBucketPublicAccessBlock	allowed	AdministratorAccess
s3:PutBucketPolicy	allowed	AdministratorAccess
s3:PutObject	allowed	AdministratorAccess
lambda:CreateFunction	allowed	AdministratorAccess
lambda:CreateFunctionUrlConfig	allowed	AdministratorAccess
lambda:AddPermission	allowed	AdministratorAccess
lambda:UpdateFunctionConfiguration	allowed	AdministratorAccess
```

## 8. IBM Cloud: cuenta y región seleccionadas (login --sso -r us-south hecho antes; código de un solo uso omitido)

_2026-11-13 11:55_ · código de salida 0

```
> C:\Users\aangu\AppData\Local\Microsoft\WinGet\Links\ibmcloud.exe target
API endpoint:      https://cloud.ibm.com
Region:            us-south
User:              andres.angulo@anahuac.mx
Account:           Andrés Angulo (f191d50cebbb4ec195285a71fedde14c) <-> 3224975
Resource group:    No resource group targeted, use 'C:\Users\aangu\AppData\Local\Microsoft\WinGet\Links\ibmcloud.exe target -g RESOURCE_GROUP'
CF API endpoint:   
Org:               
Space:
```

## 9. Instancia previa Cloudant-cr (Lite, au-syd, sin bases): borrar porque solo se permite una Lite por cuenta

_2026-11-13 11:55_ · código de salida 0

```
> C:\Users\aangu\AppData\Local\Microsoft\WinGet\Links\ibmcloud.exe resource service-instance-delete Cloudant-cr --recursive -f
Deleting service instance Cloudant-cr under account Andrés Angulo as andres.angulo@anahuac.mx...
OK
Service instance Cloudant-cr with ID crn:v1:bluemix:public:cloudantnosqldb:au-syd:a/f191d50cebbb4ec195285a71fedde14c:cfaec20f-4f60-41b7-86fb-bf732784a0d1:: is deleted successfully
```

## 10. Reclamaciones pendientes

_2026-11-13 11:55_ · código de salida 0

```
> C:\Users\aangu\AppData\Local\Microsoft\WinGet\Links\ibmcloud.exe resource reclamations
List all resource reclamations under account f191d50cebbb4ec195285a71fedde14c as andres.angulo@anahuac.mx...
OK

ID                                     Resource Instance ID                   Entity CRN                                                                                                               State       Target Time
a4431e27-847e-4e1f-b34b-ccba8de3de94   cfaec20f-4f60-41b7-86fb-bf732784a0d1   crn:v1:bluemix:public:cloudantnosqldb:au-syd:a/f191d50cebbb4ec195285a71fedde14c:cfaec20f-4f60-41b7-86fb-bf732784a0d1::   SCHEDULED   2026-11-20T17:55:29Z
```

## 11. Borrar de forma permanente la reclamación de Cloudant-cr

_2026-11-13 11:55_ · código de salida 0

```
> C:\Users\aangu\AppData\Local\Microsoft\WinGet\Links\ibmcloud.exe resource reclamation-delete a4431e27-847e-4e1f-b34b-ccba8de3de94 -f
Submitting request to delete resource reclamation a4431e27-847e-4e1f-b34b-ccba8de3de94 under account f191d50cebbb4ec195285a71fedde14c as andres.angulo@anahuac.mx...
OK
Request to delete reclamation a4431e27-847e-4e1f-b34b-ccba8de3de94 was submitted
```

## 12. Seleccionar grupo de recursos Default

_2026-11-13 11:55_ · código de salida 0

```
> C:\Users\aangu\AppData\Local\Microsoft\WinGet\Links\ibmcloud.exe target -g Default
Targeted resource group Default


                   
API endpoint:      https://cloud.ibm.com
Region:            us-south
User:              andres.angulo@anahuac.mx
Account:           Andrés Angulo (f191d50cebbb4ec195285a71fedde14c) <-> 3224975
Resource group:    Default
CF API endpoint:   
Org:               
Space:
```

## 13. Crear instancia miritmo-cloudant (plan lite, us-south, solo IAM)

_2026-11-13 11:55_ · código de salida 0

```
> C:\Users\aangu\AppData\Local\Microsoft\WinGet\Links\ibmcloud.exe resource service-instance-create miritmo-cloudant cloudantnosqldb lite us-south -p "{"legacyCredentials": false}"
Creating service instance miritmo-cloudant in resource group Default of account Andrés Angulo as andres.angulo@anahuac.mx...
OK
Service instance miritmo-cloudant was created.
                  
Name:             miritmo-cloudant
ID:               crn:v1:bluemix:public:cloudantnosqldb:us-south:a/f191d50cebbb4ec195285a71fedde14c:6dabef3a-2b91-42fe-9990-863c9ae57483::
GUID:             6dabef3a-2b91-42fe-9990-863c9ae57483
Location:         us-south
State:            provisioning
Type:             service_instance
Sub Type:         
Allow Cleanup:    false
Locked:           false
Created at:       2026-11-13T17:55:40Z
Updated at:       2026-11-13T17:55:48Z
Last Operation:             
                  Status    create in progress
                  Message   Started create instance operation
```

## 14. Instancia miritmo-cloudant activa

_2026-11-13 11:56_ · código de salida 0

```
> C:\Users\aangu\AppData\Local\Microsoft\WinGet\Links\ibmcloud.exe resource service-instance miritmo-cloudant
Retrieving service instance miritmo-cloudant in resource group Default under account Andrés Angulo as andres.angulo@anahuac.mx...
OK
                       
Name:                  miritmo-cloudant
ID:                    crn:v1:bluemix:public:cloudantnosqldb:us-south:a/f191d50cebbb4ec195285a71fedde14c:6dabef3a-2b91-42fe-9990-863c9ae57483::
GUID:                  6dabef3a-2b91-42fe-9990-863c9ae57483
Location:              us-south
Service Name:          cloudantnosqldb
Service Plan Name:     lite
Resource Group Name:   Default
State:                 active
Type:                  service_instance
Sub Type:              
Locked:                false
Created at:            2026-11-13T17:55:40Z
Created by:            andres.angulo@anahuac.mx
Updated at:            2026-11-13T17:56:06Z
Last Operation:                  
                       Status    create succeeded
                       Message   Provisioning is complete
```

## 15. Crear credencial de servicio con rol Manager

_2026-11-13 11:56_ · código de salida 0

```
> C:\Users\aangu\AppData\Local\Microsoft\WinGet\Links\ibmcloud.exe resource service-key-create miritmo-cloudant-cred Manager --instance-name miritmo-cloudant --output json
name: miritmo-cloudant-cred
state: active
role: None
crn: crn:v1:bluemix:public:cloudantnosqldb:us-south:a/f191d50cebbb4ec195285a71fedde14c:6dabef3a-2b91-42fe-9990-863c9ae57483:resource-key:b0bce5b8-36a7-438a-a64a-2c4e61e5772d
credentials.iam_role_crn: crn:v1:bluemix:public:iam::::serviceRole:Manager
(campos con credenciales omitidos)
```

## 16. Comprobar que la credencial es solo IAM (sin username/password heredados)

_2026-11-13 11:56_ · código de salida 0

```
> python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\con_cloudant.py --campos
Campos de la credencial: apikey, host, iam_apikey_description, iam_apikey_id, iam_apikey_name, iam_role_crn, iam_serviceid_crn, url, username
```

## 17. Crear las bases usuarios y registros (credenciales pasadas por variables de entorno, no se muestran)

_2026-11-13 11:56_ · código de salida 0

```
> python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\con_cloudant.py python -I "C:\Users\aangu\OneDrive\Documentos\Escuela\Anahuac\Semestre7\Cómputo en la Nube\MiRitmo\entregable-1\scripts\crear_bases_cloudant.py"
Base 'usuarios' creada.
  Base 'registros' creada.
```

## 18. S3: crear bucket privado en us-east-2

_2026-11-13 11:57_ · código de salida 0

```
> aws s3api create-bucket --bucket miritmo-frontend-5e016053 --region us-east-2 --create-bucket-configuration LocationConstraint=us-east-2 --profile miritmo
{
    "Location": "http://miritmo-frontend-5e016053.s3.amazonaws.com/",
    "BucketArn": "arn:aws:s3:::miritmo-frontend-5e016053"
}
```

## 19. S3: activar Bloquear todo el acceso público

_2026-11-13 11:57_ · código de salida 0

```
> aws s3api put-public-access-block --bucket miritmo-frontend-5e016053 --region us-east-2 --profile miritmo --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

```

## 20. S3: comprobar bloqueo de acceso público

_2026-11-13 11:57_ · código de salida 0

```
> aws s3api get-public-access-block --bucket miritmo-frontend-5e016053 --region us-east-2 --profile miritmo
{
    "PublicAccessBlockConfiguration": {
        "BlockPublicAcls": true,
        "IgnorePublicAcls": true,
        "BlockPublicPolicy": true,
        "RestrictPublicBuckets": true
    }
}
```

## 21. S3: región del bucket

_2026-11-13 11:57_ · código de salida 0

```
> aws s3api get-bucket-location --bucket miritmo-frontend-5e016053 --region us-east-2 --profile miritmo
{
    "LocationConstraint": "us-east-2"
}
```

## 22. CloudFront: crear Origin Access Control

_2026-11-13 11:57_ · código de salida 0

```
> aws cloudfront create-origin-access-control --profile miritmo --region us-east-1 --origin-access-control-config "Name=miritmo-oac,Description=OAC de MiRitmo,SigningProtocol=sigv4,SigningBehavior=always,OriginAccessControlOriginType=s3" --query OriginAccessControl.{Id:Id,Name:OriginAccessControlConfig.Name,Firma:OriginAccessControlConfig.SigningBehavior}
{
    "Id": "E2LN3JMLIJCR54",
    "Name": "miritmo-oac",
    "Firma": "always"
}
```

## 23. CloudFront: crear distribución (origen S3 con OAC, redirect-to-https, index.html)

_2026-11-13 11:57_ · código de salida 0

```
> aws cloudfront create-distribution --profile miritmo --region us-east-1 --distribution-config file://evidencias/config/cloudfront.json --query Distribution.{Id:Id,ARN:ARN,Dominio:DomainName,Estado:Status}
{
    "Id": "E1C3936GEOWFBQ",
    "ARN": "arn:aws:cloudfront::299335570017:distribution/E1C3936GEOWFBQ",
    "Dominio": "dnfx295km7eni.cloudfront.net",
    "Estado": "InProgress"
}
```

## 24. S3: política del bucket (solo la distribución E1C3936GEOWFBQ puede leer)

_2026-11-13 11:57_ · código de salida 0

```
> aws s3api put-bucket-policy --bucket miritmo-frontend-5e016053 --region us-east-2 --profile miritmo --policy file://evidencias/config/politica-bucket.json

```

## 25. S3: estado de la política (no pública)

_2026-11-13 11:57_ · código de salida 0

```
> aws s3api get-bucket-policy-status --bucket miritmo-frontend-5e016053 --region us-east-2 --profile miritmo
{
    "PolicyStatus": {
        "IsPublic": false
    }
}
```

## 26. IAM: crear rol miritmo-lambda-rol (confianza: lambda.amazonaws.com de esta cuenta)

_2026-11-13 11:57_ · código de salida 0

```
> aws iam create-role --profile miritmo --role-name miritmo-lambda-rol --description "Rol de la Lambda de MiRitmo: solo CloudWatch Logs" --assume-role-policy-document file://evidencias/config/confianza-lambda.json --query Role.{Nombre:RoleName,ARN:Arn}
{
    "Nombre": "miritmo-lambda-rol",
    "ARN": "arn:aws:iam::299335570017:role/miritmo-lambda-rol"
}
```

## 27. IAM: adjuntar solo AWSLambdaBasicExecutionRole

_2026-11-13 11:57_ · código de salida 0

```
> aws iam attach-role-policy --profile miritmo --role-name miritmo-lambda-rol --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

```

## 28. IAM: políticas del rol

_2026-11-13 11:58_ · código de salida 0

```
> aws iam list-attached-role-policies --profile miritmo --role-name miritmo-lambda-rol
{
    "AttachedPolicies": [
        {
            "PolicyName": "AWSLambdaBasicExecutionRole",
            "PolicyArn": "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        }
    ]
}
```

## 29. IAM: políticas en línea del rol (debe estar vacío)

_2026-11-13 11:58_ · código de salida 0

```
> aws iam list-role-policies --profile miritmo --role-name miritmo-lambda-rol
{
    "PolicyNames": []
}
```

## 30. Empaquetar Lambda con dependencias manylinux2014_x86_64 (Python 3.12)

_2026-11-13 11:58_ · código de salida 0

```
> python scripts/empaquetar_lambda.py
C:\Users\aangu\OneDrive\Documentos\Escuela\Anahuac\Semestre7\Cómputo en la Nube\MiRitmo\entregable-1\build\miritmo-lambda.zip: 886 archivos, 1.5 MB
```

## 31. Lambda: crear función miritmo-api (Python 3.12, x86_64, 10 s, 256 MB; variables desde archivo temporal, no se muestran)

_2026-11-13 11:59_ · código de salida 0

```
> aws lambda create-function --profile miritmo --region us-east-2 --function-name miritmo-api --runtime python3.12 --architectures x86_64 --handler lambda_function.lambda_handler --role arn:aws:iam::299335570017:role/miritmo-lambda-rol --timeout 10 --memory-size 256 --description "API de MiRitmo (Entregable 1)" --zip-file "fileb://C:\Users\aangu\OneDrive\Documentos\Escuela\Anahuac\Semestre7\Cómputo en la Nube\MiRitmo\entregable-1\build\miritmo-lambda.zip" --environment file://C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\tmpjnobf787.json --query {Nombre:FunctionName,ARN:FunctionArn,Runtime:Runtime,Arquitectura:Architectures[0],Timeout:Timeout,Memoria:MemorySize,Estado:State,Variables:keys(Environment.Variables)}
{
    "Nombre": "miritmo-api",
    "ARN": "arn:aws:lambda:us-east-2:299335570017:function:miritmo-api",
    "Runtime": "python3.12",
    "Arquitectura": "x86_64",
    "Timeout": 10,
    "Memoria": 256,
    "Estado": "Pending",
    "Variables": [
        "CLOUDANT_URL",
        "CLOUDANT_APIKEY",
        "TOKEN_SECRET",
        "ALLOWED_ORIGIN"
    ]
}
```

## 32. Lambda: crear URL de función (auth NONE) con CORS solo para el dominio de CloudFront

_2026-11-13 11:59_ · código de salida 254

```
> aws lambda create-function-url-config --profile miritmo --region us-east-2 --function-name miritmo-api --auth-type NONE --cors file://evidencias/config/cors-lambda.json
[stderr]

aws: [ERROR]: An error occurred (ValidationException) when calling the CreateFunctionUrlConfig operation: 1 validation error detected: Value '[GET, POST, PUT, OPTIONS]' at 'cors.allowMethods' failed to satisfy constraint: Member must satisfy constraint: [Member must have length less than or equal to 6, Member must have length greater than or equal to 0, Member must satisfy regular expression pattern: .*, Member must not be null]
```

## 33. Lambda: crear URL de función (auth NONE) con CORS (GET, POST, PUT; OPTIONS lo responde la URL de función automáticamente)

_2026-11-13 11:59_ · código de salida 0

```
> aws lambda create-function-url-config --profile miritmo --region us-east-2 --function-name miritmo-api --auth-type NONE --cors file://evidencias/config/cors-lambda.json
{
    "FunctionUrl": "https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws/",
    "FunctionArn": "arn:aws:lambda:us-east-2:299335570017:function:miritmo-api",
    "AuthType": "NONE",
    "Cors": {
        "AllowHeaders": [
            "content-type",
            "authorization"
        ],
        "AllowMethods": [
            "GET",
            "POST",
            "PUT"
        ],
        "AllowOrigins": [
            "https://dnfx295km7eni.cloudfront.net"
        ],
        "MaxAge": 300
    },
    "CreationTime": "2026-11-13T17:59:33.397825856Z"
}
```

## 34. Lambda: permiso público lambda:InvokeFunctionUrl (auth NONE)

_2026-11-13 11:59_ · código de salida 0

```
> aws lambda add-permission --profile miritmo --region us-east-2 --function-name miritmo-api --statement-id url-publica --action lambda:InvokeFunctionUrl --principal * --function-url-auth-type NONE
{
    "Statement": "{\"Sid\":\"url-publica\",\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":\"lambda:InvokeFunctionUrl\",\"Resource\":\"arn:aws:lambda:us-east-2:299335570017:function:miritmo-api\",\"Condition\":{\"StringEquals\":{\"lambda:FunctionUrlAuthType\":\"NONE\"}}}"
}
```

## 35. Lambda: permiso lambda:InvokeFunction solo vía URL de función

_2026-11-13 11:59_ · código de salida 0

```
> aws lambda add-permission --profile miritmo --region us-east-2 --function-name miritmo-api --statement-id url-publica-invocar --action lambda:InvokeFunction --principal * --invoked-via-function-url
{
    "Statement": "{\"Sid\":\"url-publica-invocar\",\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":\"lambda:InvokeFunction\",\"Resource\":\"arn:aws:lambda:us-east-2:299335570017:function:miritmo-api\",\"Condition\":{\"Bool\":{\"lambda:InvokedViaFunctionUrl\":\"true\"}}}"
}
```

## 36. S3: subir dia.html

_2026-11-13 12:00_ · código de salida 0

```
> aws s3 cp dia.html s3://miritmo-frontend-5e016053/dia.html --content-type "text/html; charset=utf-8" --profile miritmo --region us-east-2
Completed 4.5 KiB/4.5 KiB (12.5 KiB/s) with 1 file(s) remaining
upload: .\dia.html to s3://miritmo-frontend-5e016053/dia.html
```

## 37. S3: subir index.html

_2026-11-13 12:00_ · código de salida 0

```
> aws s3 cp index.html s3://miritmo-frontend-5e016053/index.html --content-type "text/html; charset=utf-8" --profile miritmo --region us-east-2
Completed 3.2 KiB/3.2 KiB (8.6 KiB/s) with 1 file(s) remaining
upload: .\index.html to s3://miritmo-frontend-5e016053/index.html
```

## 38. S3: subir css/estilos.css

_2026-11-13 12:00_ · código de salida 0

```
> aws s3 cp css/estilos.css s3://miritmo-frontend-5e016053/css/estilos.css --content-type "text/css; charset=utf-8" --profile miritmo --region us-east-2
Completed 7.0 KiB/7.0 KiB (22.9 KiB/s) with 1 file(s) remaining
upload: css\estilos.css to s3://miritmo-frontend-5e016053/css/estilos.css
```

## 39. S3: subir img/icono.svg

_2026-11-13 12:00_ · código de salida 0

```
> aws s3 cp img/icono.svg s3://miritmo-frontend-5e016053/img/icono.svg --content-type image/svg+xml --profile miritmo --region us-east-2
Completed 335 Bytes/335 Bytes (1.0 KiB/s) with 1 file(s) remaining
upload: img\icono.svg to s3://miritmo-frontend-5e016053/img/icono.svg
```

## 40. S3: subir js/acceso.js

_2026-11-13 12:00_ · código de salida 0

```
> aws s3 cp js/acceso.js s3://miritmo-frontend-5e016053/js/acceso.js --content-type "application/javascript; charset=utf-8" --profile miritmo --region us-east-2
Completed 2.0 KiB/2.0 KiB (6.1 KiB/s) with 1 file(s) remaining
upload: js\acceso.js to s3://miritmo-frontend-5e016053/js/acceso.js
```

## 41. S3: subir js/comun.js

_2026-11-13 12:00_ · código de salida 0

```
> aws s3 cp js/comun.js s3://miritmo-frontend-5e016053/js/comun.js --content-type "application/javascript; charset=utf-8" --profile miritmo --region us-east-2
Completed 4.2 KiB/4.2 KiB (14.0 KiB/s) with 1 file(s) remaining
upload: js\comun.js to s3://miritmo-frontend-5e016053/js/comun.js
```

## 42. S3: subir js/config.js

_2026-11-13 12:00_ · código de salida 0

```
> aws s3 cp js/config.js s3://miritmo-frontend-5e016053/js/config.js --content-type "application/javascript; charset=utf-8" --profile miritmo --region us-east-2
Completed 244 Bytes/244 Bytes (571 Bytes/s) with 1 file(s) remaining
upload: js\config.js to s3://miritmo-frontend-5e016053/js/config.js
```

## 43. S3: subir js/dia.js

_2026-11-13 12:00_ · código de salida 0

```
> aws s3 cp js/dia.js s3://miritmo-frontend-5e016053/js/dia.js --content-type "application/javascript; charset=utf-8" --profile miritmo --region us-east-2
Completed 3.4 KiB/3.4 KiB (10.4 KiB/s) with 1 file(s) remaining
upload: js\dia.js to s3://miritmo-frontend-5e016053/js/dia.js
```

## 44. S3: objetos del bucket

_2026-11-13 12:00_ · código de salida 0

```
> aws s3api list-objects-v2 --bucket miritmo-frontend-5e016053 --profile miritmo --region us-east-2 --query Contents[].[Key,Size] --output text
css/estilos.css	7157
dia.html	4566
img/icono.svg	335
index.html	3325
js/acceso.js	2083
js/comun.js	4340
js/config.js	244
js/dia.js	3508
```

## 45. CloudFront: invalidar /*

_2026-11-13 12:00_ · código de salida 0

```
> aws cloudfront create-invalidation --profile miritmo --region us-east-1 --distribution-id E1C3936GEOWFBQ --paths /* --query Invalidation.{Id:Id,Estado:Status}
{
    "Id": "IC2RMBT2FGCTI1U7F8D8B5SP28",
    "Estado": "InProgress"
}
```

## 46. CloudFront: estado de la distribución

_2026-11-13 12:00_ · código de salida 0

```
> aws cloudfront get-distribution --id E1C3936GEOWFBQ --profile miritmo --region us-east-1 --query Distribution.{Estado:Status,Habilitada:DistributionConfig.Enabled,Dominio:DomainName,Raiz:DistributionConfig.DefaultRootObject,Protocolo:DistributionConfig.DefaultCacheBehavior.ViewerProtocolPolicy,OAC:DistributionConfig.Origins.Items[0].OriginAccessControlId}
{
    "Estado": "Deployed",
    "Habilitada": true,
    "Dominio": "dnfx295km7eni.cloudfront.net",
    "Raiz": "index.html",
    "Protocolo": "redirect-to-https",
    "OAC": "E2LN3JMLIJCR54"
}
```

## 47. Prueba: HTTP redirige a HTTPS

_2026-11-13 12:00_ · código de salida 0

```
> curl.exe -s -o NUL -w "%{http_code} -> %{redirect_url}" http://dnfx295km7eni.cloudfront.net/
301 -> https://dnfx295km7eni.cloudfront.net/
```

## 48. Prueba: HTTPS sirve index.html y config.js

_2026-11-13 12:00_ · código de salida 0

```
> curl.exe -s -o NUL -w "index: %{http_code} %{content_type}" https://dnfx295km7eni.cloudfront.net/
index: 200 text/html; charset=utf-8
```

## 49. Prueba: el bucket S3 no es accesible directo

_2026-11-13 12:00_ · código de salida 0

```
> curl.exe -s -o NUL -w %{http_code} https://miritmo-frontend-5e016053.s3.us-east-2.amazonaws.com/index.html
403
```

## 50. Cloudant: registro de A sigue en 84 tras el intento de B

_2026-11-13 12:02_ · código de salida 0

```
> python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\con_cloudant.py python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\cloudant_util.py ver registros pruebaa-20261113120150@miritmo.mx:2026-11-13
{"_id": "pruebaa-20261113120150@miritmo.mx:2026-11-13", "usuario": "pruebaa-20261113120150@miritmo.mx", "fecha": "2026-11-13", "horas_trabajo": 6.0, "tareas": 4, "horas_sueno": 7.5, "energia": 4, "calificacion": 84, "actualizado": "2026-11-13T18:01:56+00:00"}
```

## 51. Cloudant: el registro de B quedó con usuario=B (se ignoró usuario=A del cuerpo)

_2026-11-13 12:02_ · código de salida 0

```
> python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\con_cloudant.py python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\cloudant_util.py ver registros pruebab-20261113120150@miritmo.mx:2026-11-13
{"_id": "pruebab-20261113120150@miritmo.mx:2026-11-13", "usuario": "pruebab-20261113120150@miritmo.mx", "fecha": "2026-11-13", "horas_trabajo": 0.0, "tareas": 0, "horas_sueno": 0.0, "energia": 1, "calificacion": 10, "actualizado": "2026-11-13T18:01:59+00:00"}
```

## 52. Cloudant: documento de usuario (hash y sal, sin contraseña)

_2026-11-13 12:02_ · código de salida 0

```
> python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\con_cloudant.py python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\cloudant_util.py ver usuarios pruebaa-20261113120150@miritmo.mx
{"_id": "pruebaa-20261113120150@miritmo.mx", "nombre": "Prueba A", "correo": "pruebaa-20261113120150@miritmo.mx", "hash": "893fcad5591cba62099cf7b559bcc83ef745d4f21ce0edaca076cfa91cbb612d", "sal": "0f7eb312af4b988aa0efed271903829e", "creado": "2026-11-13T18:01:51+00:00"}
```

## 53. Pruebas de aceptación con curl (RF-01 a RF-04 y RNF-02)

_2026-11-13 12:02_ · código de salida 0

```
> powershell -ExecutionPolicy Bypass -File evidencias\pruebas_curl.ps1
MiRitmo - pruebas con curl contra https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws
Hoy (CDMX): 2026-11-13

[OK ] RF-01   Crear cuenta nueva                                         HTTP 201  token recibido (oculto)
[OK ] RF-01   Crear cuenta con el mismo correo                           HTTP 409  Ya existe una cuenta con ese correo.
[OK ] RF-01   Crear cuenta con contraseña de 7 caracteres                HTTP 400  Revisa los datos marcados.
[OK ] RF-02   Iniciar sesión con datos correctos                         HTTP 200  token recibido (oculto)
[OK ] RF-02   Iniciar sesión con contraseña incorrecta                   HTTP 401  Correo o contraseña incorrectos.
[OK ] RF-03   Guardar registro de hoy (2026-11-13)                       HTTP 200  calificación 71
[OK ] RF-03   Guardar registro con fecha futura (2026-11-14)             HTTP 400  No puedes registrar días futuros.
[OK ] RF-03   Guardar registro de hace 7 días (2026-11-06)               HTTP 400  Solo puedes registrar hoy o los 6 días anteriores.
[OK ] RF-04   6 h, 4 tareas, 7.5 h sueño, energía 4 (esperado 84)        HTTP 200  calificación 84
[OK ] RNF-02  PUT sin token                                              HTTP 401  Tu sesión no es válida o expiró. Inicia sesión de nuevo.
[OK ] RNF-02  PUT con token alterado                                     HTTP 401  Tu sesión no es válida o expiró. Inicia sesión de nuevo.
[OK ] RNF-02  Usuario B manda usuario=A en el cuerpo (se guarda como B)  HTTP 200  calificación 10
[OK ] RNF-02  Usuario B intenta la ruta /registros/<correo A>:<fecha>    HTTP 400  Fecha inválida.

Resultado: 13 de 13 pruebas como se esperaba.
Cuentas de prueba: pruebaA-20261113120232@miritmo.mx y pruebaB-20261113120232@miritmo.mx
```

## 54. CORS: petición desde un origen que no es CloudFront

_2026-11-13 12:02_ · código de salida 0

```
> curl.exe -s -w " HTTP %{http_code}" -X POST https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws/sesiones -H "Origin: https://otro-sitio.example" -H "content-type: application/json" --data-binary {}
{"error": "Origen no permitido."} HTTP 403
```

## 55. CORS: preflight desde CloudFront

_2026-11-13 12:02_ · código de salida 0

```
> curl.exe -s -o NUL -D - -X OPTIONS https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws/registros/2026-11-13 -H "Origin: https://dnfx295km7eni.cloudfront.net" -H "Access-Control-Request-Method: PUT" -H "Access-Control-Request-Headers: authorization,content-type"
HTTP/1.1 200 OK
Date: Fri, 13 Nov 2026 18:02:55 GMT
Content-Type: application/json
Content-Length: 0
Connection: keep-alive
x-amzn-RequestId: 4755815b-667d-43fd-9e9a-675fde536d3a
Access-Control-Allow-Origin: https://dnfx295km7eni.cloudfront.net
Access-Control-Allow-Headers: content-type,authorization
Vary: Origin
Access-Control-Allow-Methods: GET,POST,PUT
Access-Control-Max-Age: 300
```

## 56. CloudWatch Logs: grupo de la función

_2026-11-13 12:02_ · código de salida 0

```
> aws logs describe-log-groups --profile miritmo --region us-east-2 --log-group-name-prefix /aws/lambda/miritmo-api --query logGroups[].[logGroupName,arn] --output text
/aws/lambda/miritmo-api	arn:aws:logs:us-east-2:299335570017:log-group:/aws/lambda/miritmo-api:*
```

## 57. CloudWatch Logs: buscar errores (Traceback, ERROR, Task timed out)

_2026-11-13 12:03_ · código de salida 0

```
> aws logs filter-log-events --profile miritmo --region us-east-2 --log-group-name /aws/lambda/miritmo-api --filter-pattern "?Traceback ?ERROR ?"Task timed out"" --query length(events)
0
```

## 58. CloudWatch Logs: últimas líneas REPORT (duración y memoria)

_2026-11-13 12:03_ · código de salida 0

```
> aws logs filter-log-events --profile miritmo --region us-east-2 --log-group-name /aws/lambda/miritmo-api --filter-pattern REPORT --query events[-3:].message --output text
REPORT RequestId: 721c3476-35c0-4dc0-8062-1aea3fe75298	Duration: 80.90 ms	Billed Duration: 81 ms	Memory Size: 256 MB	Max Memory Used: 99 MB	
	REPORT RequestId: 12bb6917-c4b9-423c-86c5-d81b38e495da	Duration: 1.65 ms	Billed Duration: 2 ms	Memory Size: 256 MB	Max Memory Used: 99 MB	
	REPORT RequestId: 7427fa22-b5d5-493b-88b2-8d4d28f8abbc	Duration: 7.95 ms	Billed Duration: 8 ms	Memory Size: 256 MB	Max Memory Used: 99 MB
```

## 59. Cuenta demo creada (demo@miritmo.mx, contraseña no registrada) con registro de hoy = 84; documento en Cloudant

_2026-11-13 12:03_ · código de salida 0

```
> python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\con_cloudant.py python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\cloudant_util.py ver registros demo@miritmo.mx:2026-11-13
{"_id": "demo@miritmo.mx:2026-11-13", "usuario": "demo@miritmo.mx", "fecha": "2026-11-13", "horas_trabajo": 6.0, "tareas": 4, "horas_sueno": 7.5, "energia": 4, "calificacion": 84, "actualizado": "2026-11-13T18:03:19+00:00"}
```

## 60. Cloudant: borrar cuentas y registros de prueba (_id que empieza con 'prueba')

_2026-11-13 12:03_ · código de salida 0

```
> python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\con_cloudant.py python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\cloudant_util.py borrar-prefijo prueba
borrado usuarios/pruebaa-20261113120150@miritmo.mx
borrado usuarios/pruebaa-20261113120232@miritmo.mx
borrado usuarios/pruebab-20261113120150@miritmo.mx
borrado usuarios/pruebab-20261113120232@miritmo.mx
borrado registros/pruebaa-20261113120150@miritmo.mx:2026-11-13
borrado registros/pruebaa-20261113120232@miritmo.mx:2026-11-13
borrado registros/pruebab-20261113120150@miritmo.mx:2026-11-13
borrado registros/pruebab-20261113120232@miritmo.mx:2026-11-13
```

## 61. Cloudant: documentos que quedan

_2026-11-13 12:03_ · código de salida 0

```
> python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\con_cloudant.py python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\cloudant_util.py listar
usuarios: ['demo@miritmo.mx']
registros: ['demo@miritmo.mx:2026-11-13']
```

## 62. Reempaquetar Lambda (corrección CORS duplicado)

_2026-11-13 12:06_ · código de salida 1

```
> python scripts/empaquetar_lambda.py
[stderr]
Traceback (most recent call last):
  File "C:\Users\aangu\OneDrive\Documentos\Escuela\Anahuac\Semestre7\Cómputo en la Nube\MiRitmo\entregable-1\scripts\empaquetar_lambda.py", line 48, in <module>
    main()
  File "C:\Users\aangu\OneDrive\Documentos\Escuela\Anahuac\Semestre7\Cómputo en la Nube\MiRitmo\entregable-1\scripts\empaquetar_lambda.py", line 22, in main
    os.makedirs(PAQUETE)
  File "<frozen os>", line 225, in makedirs
FileExistsError: [WinError 183] No se puede crear un archivo que ya existe: 'C:\\Users\\aangu\\OneDrive\\Documentos\\Escuela\\Anahuac\\Semestre7\\Cómputo en la Nube\\MiRitmo\\entregable-1\\build\\paquete'
```

## 63. Lambda: actualizar código (las variables de entorno no cambian)

_2026-11-13 12:06_ · código de salida 0

```
> aws lambda update-function-code --profile miritmo --region us-east-2 --function-name miritmo-api --zip-file fileb://build/miritmo-lambda.zip --query {Nombre:FunctionName,Estado:LastUpdateStatus,CodeSha256:CodeSha256}
{
    "Nombre": "miritmo-api",
    "Estado": "InProgress",
    "CodeSha256": "dR7q2P2fEPGZZPwKYaFhVFtftW6T4drtv5d2guAscMg="
}
```

## 64. CORS: respuesta real desde el origen de CloudFront (un solo Access-Control-Allow-Origin)

_2026-11-13 12:07_ · código de salida 0

```
> curl.exe -s -D - -o NUL -X POST https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws/sesiones -H "Origin: https://dnfx295km7eni.cloudfront.net" -H "content-type: application/json" --data-binary {}
HTTP/1.1 400 Bad Request
Date: Fri, 13 Nov 2026 18:06:59 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 124
Connection: keep-alive
x-amzn-RequestId: 9ec307e0-1714-488e-a78f-bbe6a1b72abd
access-control-allow-origin: https://dnfx295km7eni.cloudfront.net
access-control-allow-origin: https://dnfx295km7eni.cloudfront.net
access-control-allow-headers: Content-Type,Authorization
vary: Origin
vary: Origin
access-control-allow-methods: GET,POST,PUT,OPTIONS
X-Amzn-Trace-Id: Root=1-6af751c3-09e6d6561fc1954407007d08;Parent=76a4588a0cbdc884;Sampled=0;Lineage=1:37881594:0
access-control-max-age: 86400
```

## 65. Reempaquetar Lambda en carpeta temporal (corrección CORS duplicado)

_2026-11-13 12:07_ · código de salida 0

```
> python scripts/empaquetar_lambda.py
C:\Users\aangu\OneDrive\Documentos\Escuela\Anahuac\Semestre7\Cómputo en la Nube\MiRitmo\entregable-1\build\miritmo-lambda.zip: 886 archivos, 1.5 MB
```

## 66. Lambda: actualizar código (las variables de entorno no cambian)

_2026-11-13 12:07_ · código de salida 0

```
> aws lambda update-function-code --profile miritmo --region us-east-2 --function-name miritmo-api --zip-file fileb://build/miritmo-lambda.zip --query {Nombre:FunctionName,Estado:LastUpdateStatus,CodeSha256:CodeSha256}
{
    "Nombre": "miritmo-api",
    "Estado": "InProgress",
    "CodeSha256": "s05LVtBa1poOz3Lm3vLW6vw4cubyheUsv9ewn976bx8="
}
```

## 67. CORS: respuesta real desde el origen de CloudFront (un solo Access-Control-Allow-Origin)

_2026-11-13 12:07_ · código de salida 0

```
> curl.exe -s -D - -o NUL -X POST https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws/sesiones -H "Origin: https://dnfx295km7eni.cloudfront.net" -H "content-type: application/json" --data-binary {}
HTTP/1.1 400 Bad Request
Date: Fri, 13 Nov 2026 18:07:34 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 124
Connection: keep-alive
x-amzn-RequestId: 3b09ce6a-90eb-449e-af5a-69df09287402
Access-Control-Allow-Origin: https://dnfx295km7eni.cloudfront.net
Vary: Origin
X-Amzn-Trace-Id: Root=1-6af751e6-223e05072eb0208c5eb3bce6;Parent=2f618a104007f5c4;Sampled=0;Lineage=1:37881594:0
```

## 68. Cloudant: borrar cuentas de prueba creadas para la captura 14

_2026-11-13 12:36_ · código de salida 0

```
> python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\con_cloudant.py python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\cloudant_util.py borrar-prefijo prueba
borrado usuarios/pruebaa-20261113123606@miritmo.mx
borrado usuarios/pruebab-20261113123606@miritmo.mx
borrado registros/pruebaa-20261113123606@miritmo.mx:2026-11-13
borrado registros/pruebab-20261113123606@miritmo.mx:2026-11-13
```

## 69. Cloudant: documentos finales (solo la cuenta demo)

_2026-11-13 12:36_ · código de salida 0

```
> python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\con_cloudant.py python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\cloudant_util.py listar
usuarios: ['demo@miritmo.mx']
registros: ['demo@miritmo.mx:2026-11-13']
```

## 70. CloudWatch Logs: revisión final de errores (después de la corrección CORS y de todas las pruebas)

_2026-11-13 12:37_ · código de salida 0

```
> aws logs filter-log-events --profile miritmo --region us-east-2 --log-group-name /aws/lambda/miritmo-api --filter-pattern "?Traceback ?ERROR" --query length(events)
0
```

## 71. Lambda: configuración final (sin valores de variables)

_2026-11-13 12:37_ · código de salida 0

```
> aws lambda get-function-configuration --profile miritmo --region us-east-2 --function-name miritmo-api --query {Nombre:FunctionName,Runtime:Runtime,Arquitectura:Architectures[0],Timeout:Timeout,Memoria:MemorySize,Rol:Role,Estado:State,Variables:keys(Environment.Variables)}
{
    "Nombre": "miritmo-api",
    "Runtime": "python3.12",
    "Arquitectura": "x86_64",
    "Timeout": 10,
    "Memoria": 256,
    "Rol": "arn:aws:iam::299335570017:role/miritmo-lambda-rol",
    "Estado": "Active",
    "Variables": [
        "CLOUDANT_URL",
        "CLOUDANT_APIKEY",
        "TOKEN_SECRET",
        "ALLOWED_ORIGIN"
    ]
}
```
