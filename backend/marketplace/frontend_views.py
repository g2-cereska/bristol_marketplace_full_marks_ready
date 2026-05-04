from django.views.generic import TemplateView


class CatalogueView(TemplateView):
    template_name = "marketplace/catalogue.html"


class CartView(TemplateView):
    template_name = "marketplace/cart.html"


class OrdersView(TemplateView):
    template_name = "marketplace/orders.html"


class ProducerHubView(TemplateView):
    template_name = "marketplace/producer.html"


class LoginPageView(TemplateView):
    template_name = "marketplace/login.html"