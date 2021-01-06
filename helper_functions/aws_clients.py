import boto3


class AWSClients:
    """All the required oauth and api keys are stored in ssm parameters and are fetched where ever required."""
    def __init__(self):
        self.client = boto3.client('ssm')

    def weather_api(self):
        response = self.client.get_parameter(Name='/Jarvis/weather_api', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def news_api(self):
        response = self.client.get_parameter(Name='/Jarvis/news_api', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def robinhood_user(self):
        response = self.client.get_parameter(Name='/Jarvis/robinhood_user', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def robinhood_pass(self):
        response = self.client.get_parameter(Name='/Jarvis/robinhood_pass', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def robinhood_qr(self):
        response = self.client.get_parameter(Name='/Jarvis/robinhood_qr', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def icloud_pass(self):
        response = self.client.get_parameter(Name='/Jarvis/icloud_pass', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def icloud_recovery(self):
        response = self.client.get_parameter(Name='/Jarvis/icloud_recovery', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def icloud_user(self):
        response = self.client.get_parameter(Name='/Jarvis/icloud_user', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def gmail_user(self):
        response = self.client.get_parameter(Name='/Jarvis/gmail_user', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def gmail_pass(self):
        response = self.client.get_parameter(Name='/Jarvis/gmail_pass', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def phone(self):
        response = self.client.get_parameter(Name='/Jarvis/phone', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def maps_api(self):
        response = self.client.get_parameter(Name='/Jarvis/maps_api', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def git_user(self):
        response = self.client.get_parameter(Name='/Jarvis/git_user', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def git_pass(self):
        response = self.client.get_parameter(Name='/Jarvis/git_pass', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def tv_mac(self):
        response = self.client.get_parameter(Name='/Jarvis/tv_mac', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def tv_ip(self):
        response = self.client.get_parameter(Name='/Jarvis/tv_ip', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def tv_client_key(self):
        response = self.client.get_parameter(Name='/Jarvis/tv_client_key', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val

    def birthday(self):
        response = self.client.get_parameter(Name='/Jarvis/birthday', WithDecryption=True)
        param = response['Parameter']
        val = param['Value']
        return val
