from django.shortcuts import render , redirect
from django.views.generic import View ,TemplateView , CreateView , DetailView ,ListView
from django.urls import reverse_lazy
from .forms import CheckoutForm , CustomerRegistrationForm ,CustomerLoginForm
from .models import *
from django.contrib.auth import authenticate , login ,logout
from django.views.generic.edit import FormView


class EcomMixin(object):
    def dispatch(self, request, *args, **kwargs):
        cart_id = request.session.get("cart_id")
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            if request.user.is_authenticated and request.user.customer:
                cart_obj.customer = request.user.customer
                cart_obj.save()
        return super().dispatch(request, *args, **kwargs)
    

class HomeView(EcomMixin, TemplateView):
    template_name = "home.html"
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        # context['myname'] = "Akshay Garg"
        # for showing last added product on top we use .order_by("-id")
        context['product_list'] = Product.objects.all().order_by("-id")
        return context

# For showing all prodcut category wise

class AllProductsView(EcomMixin ,TemplateView):
    template_name = "allproducts.html"
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        context['allcategories'] = Category.objects.all()
        return context
    
    
class ProductDetailView(EcomMixin,TemplateView):
    template_name = "productdetail.html"
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        url_slug =self.kwargs['slug']
        product= Product.objects.get(slug=url_slug)
        product.view_count += 1  # for increasing the view count
        product.save()           # save that increaded view in our db
        context['product'] = product
        return context
        
class AddToCartView(EcomMixin,TemplateView):
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
     
     
class ManageCartView(EcomMixin , View):
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

class EmptyCartView(EcomMixin ,View):
    def get(self,request,*args,**kwargs):
        cart_id = request.session.get("cart_id",None)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
            cart.cartproduct_set.all().delete()
            cart.total=0
            cart.save()
        return redirect("mycart")
     
class MyCartView(EcomMixin ,TemplateView):
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

class CheckoutView(EcomMixin ,CreateView):
    template_name = "checkout.html"
    form_class = CheckoutForm
    success_url = reverse_lazy("home")
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.customer:
            pass
        else:
            return redirect("/login/?next=/checkout/")
        return super().dispatch(request, *args, **kwargs)
    
    
    def get_context_data(self , **kwargs):
        context = super().get_context_data(**kwargs)
        cart_id = self.request.session.get("cart_id",None)
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
        else:
            cart_obj = None
        context['cart'] = cart_obj
        return context
    
    def form_valid(self,form):
        cart_id = self.request.session.get("cart_id")
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            form.instance.cart = cart_obj
            form.instance.subtotal = cart_obj.total
            form.instance.discount = 0
            form.instance.total = cart_obj.total
            form.instance.order_status = "Order Received"
            del self.request.session['cart_id']
        else:
            return redirect("home")
        
        return super().form_valid(form)

class CustomerRegistrationView(CreateView):
    template_name = "customerregistration.html"
    form_class = CustomerRegistrationForm
    success_url = reverse_lazy("home")
      
    def get_success_url(self):
        if "next" in self.request.GET:
            next_url = self.request.GET.get("next")
            return next_url
        else:
            return self.success_url
    
    def form_valid(self , form):
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        email = form.cleaned_data.get("email")
        user = User.objects.create_user(username , email , password)
        form.instance.user = user
        login(self.request , user)
        return super().form_valid(form)
  
        
# Logout
class CustomerLogoutView(View):
    def get(self , request):
        logout(request)
        return redirect("home")
# Login
class CustomerLoginview(FormView):
    template_name = "customerlogin.html"
    form_class = CustomerLoginForm
    success_url = reverse_lazy("home")
    
    # form_valid method is a type of post method and is available in formviw and createview
    def form_valid(self,form):
        uname = form.cleaned_data.get("username")
        pword = form.cleaned_data.get("password")
        usr = authenticate(username=uname , password=pword)
        if usr is not None and Customer.objects.filter(user=usr).exists():
            login(self.request,usr)
        else:
            return render(self.request , "customerlogin.html" ,{"form":CustomerLoginForm , "error":"invalid credential"})
        return super().form_valid(form)
    # for haadnling the ?next= we need to modify the succes_url
    def get_success_url(self):
        if "next" in self.request.GET:
            next_url = self.request.GET.get("next")
            return next_url
        else:
            return self.success_url


    
class AboutView(EcomMixin ,TemplateView):
    template_name = "about.html"
    
class ContactView(EcomMixin ,TemplateView):
    template_name = "contactus.html"
    

class CustomerProfileView(TemplateView):
    template_name = "customerprofile.html"
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
            pass
        else:
            return redirect("/login/?next=/profile/")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self , **kwargs):
        context = super().get_context_data()
        # for customer detail
        customer = self.request.user.customer
        context['customer'] = customer
        # for previous orders
        orders = Order.objects.filter(cart__customer=customer).order_by("-id")
        context['orders'] = orders
        return context
    
class CustomerOrderDetailView(DetailView):
    template_name = "customerorderdetail.html"
    model = Order
    context_object_name = "ord_obj"
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
            order_id = self.kwargs["pk"]
            order = Order.objects.get(id=order_id)
            if request.user.customer != order.cart.customer:
                return redirect("/profile/")
        else:
            return redirect("/login/?next=/profile/")
        return super().dispatch(request, *args, **kwargs)
    
    
# Admin pages
class AdminLoginView(FormView):
    template_name = "adminpages/adminlogin.html"
    form_class = CustomerLoginForm
    success_url = reverse_lazy("adminhome")
    
    def form_valid(self , form):
        uname = form.cleaned_data.get("username")
        pword = form.cleaned_data.get("password")
        usr = authenticate(username=uname , password=pword)
        if usr is not None and Admin.objects.filter(user=usr).exists():
            login(self.request,usr)
        else:
            return render(self.request , self.template_name ,{"form":self.form_class , "error":"invalid credential"})
        return super().form_valid(form)
    
    
    
class AdminRequiredMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Admin.objects.filter(user=request.user).exists():
            pass
        else:
            return redirect("/admin-login")
        return super().dispatch(request, *args, **kwargs)
    
class AdminHomeView(AdminRequiredMixin , TemplateView):
    template_name = "adminpages/adminhome.html"
    
    def get_context_data(self , **kwargs):
        context = super().get_context_data(**kwargs)
        context["pendingorders"] = Order.objects.filter(order_status="Order Received").order_by("-id")
        
        return context
    
class AdminOrderDetailView(AdminRequiredMixin , DetailView):
    template_name = "adminpages/adminorderdetail.html"
    model = Order 
    context_object_name = "ord_obj"   
    
class AdminOrderListView(AdminRequiredMixin , ListView):
    template_name = "adminpages/adminorderlist.html"
    queryset = Order.objects.all().order_by("-id")
    context_object_name ="allorders"
    
    
    
    
    
    
    
    
    