import boto3


class AWSClients:
    client = boto3.client('ssm')

    def weather_api(self):
        response = AWSClients.client.get_parameter(Name='/Jarvis/weather_api', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def news_api(self):
        response = AWSClients.client.get_parameter(Name='/Jarvis/news_api', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def robinhood_user(self):
        response = AWSClients.client.get_parameter(Name='/Jarvis/robinhood_user', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def robinhood_pass(self):
        response = AWSClients.client.get_parameter(Name='/Jarvis/robinhood_pass', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def robinhood_qr(self):
        response = AWSClients.client.get_parameter(Name='/Jarvis/robinhood_qr', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def icloud_pass(self):
        response = AWSClients.client.get_parameter(Name='/Jarvis/icloud_pass', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def icloud_recovery(self):
        response = AWSClients.client.get_parameter(Name='/Jarvis/icloud_recovery', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def icloud_user(self):
        response = AWSClients.client.get_parameter(Name='/Jarvis/icloud_user', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def gmail_user(self):
        response = AWSClients.client.get_parameter(Name='/Jarvis/gmail_user', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def gmail_pass(self):
        response = AWSClients.client.get_parameter(Name='/Jarvis/gmail_pass', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def remind(self):
        response = AWSClients.client.get_parameter(Name='/Jarvis/remind', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def maps_api(self):
        response = AWSClients.client.get_parameter(Name='/Jarvis/maps_api', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val
