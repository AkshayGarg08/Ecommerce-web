from django.shortcuts import render , redirect
from django.views.generic import View ,TemplateView
from .models import *

# Create your views here.
class HomeView(TemplateView):
    template_name = "home.html"
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        # context['myname'] = "Akshay Garg"
        # for showing last added product on top we use .order_by("-id")
        context['product_list'] = Product.objects.all().order_by("-id")
        return context

# For showing all prodcut category wise

class AllProductsView(TemplateView):
    template_name = "allproducts.html"
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        context['allcategories'] = Category.objects.all()
        return context
    
    
class ProductDetailView(TemplateView):
    template_name = "productdetail.html"
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        url_slug =self.kwargs['slug']
        product= Product.objects.get(slug=url_slug)
        product.view_count += 1  # for increasing the view count
        product.save()           # save that increaded view in our db
        context['product'] = product
        return context
        
class AddToCartView(TemplateView):
    template_name = "addtocart.html"
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        
        # get product id from requested url
        product_id = self.kwargs['pro_id']
        
        # get the product
        product_obj = Product.objects.get(id=product_id)
        
        #check if cart exists
        cart_id = self.request.session.get("cart_id",None)
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            this_product_in_cart = cart_obj.cartproduct_set.filter(
                product=product_obj)
            # item already exist in cart
            if this_product_in_cart.exists():
                cartproduct = this_product_in_cart.last()
                cartproduct.quantity += 1
                cartproduct.subtotal += product_obj.selling_price
                cartproduct.save()
                cart_obj.total += product_obj.selling_price
                cart_obj.save()
            # if the item in cart does not exist
            # we need to create new cartproduct
            else:
                cartproduct = CartProduct.objects.create(
                    cart=cart_obj , product=product_obj, rate=product_obj.selling_price, quantity=1 , subtotal=product_obj.selling_price)
                cart_obj.total += product_obj.selling_price
                cart_obj.save()                   
        else:
            cart_obj = Cart.objects.create(total=0)
            self.request.session['cart_id'] = cart_obj.id
            cartproduct = CartProduct.objects.create(
                    cart=cart_obj , product=product_obj, rate=product_obj.selling_price, quantity=1 , subtotal=product_obj.selling_price)
            cart_obj.total += product_obj.selling_price
            cart_obj.save()
        
        return context
     
     
class ManageCartView(View):
    def get(self,request,*args,**kwargs):
        cp_id = self.kwargs["cp_id"]      #cp_id i.e passed in the url <int:cp_id>
        action = request.GET.get("action")
        cp_obj = CartProduct.objects.get(id=cp_id)
        cart_obj = cp_obj.cart
        # condition for increment quantity
        if action == 'inc':
            cp_obj.quantity += 1
            cp_obj.subtotal += cp_obj.rate
            cp_obj.save()
            cart_obj.total += cp_obj.rate
            cart_obj.save() 
        # condition for decrement quantity
        elif action =='dcr':
            cp_obj.quantity -= 1
            cp_obj.subtotal -= cp_obj.rate
            cp_obj.save()
            cart_obj.total -= cp_obj.rate
            cart_obj.save()
            if cp_obj.quantity == 0:
                cp_obj.delete()
        # condition for delete product from cart
        elif action=='rmv':
            cart_obj.total -= cp_obj.subtotal
            cart_obj.save()
            cp_obj.delete()
        else:
            pass
        return redirect("mycart")

class EmptyCartView(View):
    def get(self,request,*args,**kwargs):
        cart_id = request.session.get("cart_id",None)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
            cart.cartproduct_set.all().delete()
            cart.total=0
            cart.save()
        return redirect("mycart")
     
class MyCartView(TemplateView):
    template_name = 'mycart.html'
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        # first take the cart id from session
        cart_id = self.request.session.get("cart_id",None)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
        else:
            cart = None
        context['cart'] = cart
        return context

  
    
    
class AboutView(TemplateView):
    template_name = "about.html"
    
class ContactView(TemplateView):
    template_name = "contactus.html"
    

