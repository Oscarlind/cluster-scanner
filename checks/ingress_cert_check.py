#!/usr/bin/python3
import datetime
import ssl
from prettytable import PrettyTable
import OpenSSL

## WIP to get the api in a cleaner way
# hostname = config.list_kube_config_contexts()[1]['context']['cluster'][:-5]
# Add a ssl timeout when time.
# Checking to see if ingress is using custom certificate and if so, when it expires
def ingress_check(dyn_client):
    v1_routes = dyn_client.resources.get(api_version='route.openshift.io/v1', kind='Route')
    ingress_cert_table = PrettyTable(['Issued to', 'Issued by', 'Expiration date'])
    route_spec = v1_routes.get(namespace='openshift-console', name='console')
    hostname = route_spec.spec.host
    cert = ssl.get_server_certificate((hostname, 443))
    x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
    x509.get_subject().get_components()
    # Expiration date
    certExpires = datetime.datetime.strptime(x509.get_notAfter().decode('ascii'), '%Y%m%d%H%M%SZ')
    # Issued to:
    x509_subject = x509.get_subject()
    common_name = x509_subject.commonName
    # Issuer:
    x509_issuer = x509.get_issuer()
    issuer_common_name = x509_issuer.commonName
    daysToExpiration = (certExpires - datetime.datetime.now()).days
    ingress_cert_table.add_row([common_name, issuer_common_name, certExpires])
    if 'ingress-operator' in issuer_common_name:
        print("\033[93m\nIngress certificate: OPENSHIFT GENERATED INGRESS CERTIFCATE IN USE: Please configure a custom certificate \033[0m\n\n",ingress_cert_table, "\n\nDays until expiration: ",daysToExpiration,)
    else:
        print("\033[95m\nIngress certificate: \033[0m\n\n",ingress_cert_table, "\n\nDays until expiration: ",daysToExpiration)

### Needs rethinking. For example, the nginx ingress controller is using "Kind=NginxIngressController" in its own NS. Either look at namespace labels or route labels?
# Quick scan to see if router-sharding is being used.
    v1_ingress_controllers = dyn_client.resources.get(api_version='operator.openshift.io/v1', kind='IngressController')
    nr_of_ingress_controllers = len(v1_ingress_controllers.get().items)
    if nr_of_ingress_controllers >= 2:
        print("\nRouter-sharding detected, number of ingress controllers: ",nr_of_ingress_controllers)
    else:
        print("\nRouter-sharding was not detected")