
class TemplateManager():

    def __init__(self):
        self.templates = {}
    
    def add_template(self, template_name: str, template: dict):
        self.templates[template_name] = template
    
