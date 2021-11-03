from django import template
from django.utils.safestring import mark_safe
from django.shortcuts import get_object_or_404
from ..models import UserProfile, Order

from ..models import User

register = template.Library()


@register.simple_tag
def MiniProfile(request):
    items = UserProfile.objects.filter(user_id=request.user.id)
    ordered = Order.objects.filter(user_id=request.user.id).exclude(status='D').count()


    if items:
        for i in items:
            items_div = """
          <div class="center">
                <div class="profile">
                    <div class="image">
                        <div class="circle-1"></div>
                        <div class="circle-2"></div>
                        <img src="/media/{}" width="70" height="70" >
                    </div>
                    
                    <div class="name">{}</div>
                    <div class="job">{}</div>
                    
                    <div class="actions">
                        <button class="btn">Test btn</button>
                        <a class="btn" href="/accounts/logout/">Logout</a>
                    </div>
                </div>
                
                <div class="stats">
                    <div class="box">
                        <span class="value">523</span>
                        <span class="parameter">Posts</span>
                    </div>
                    <div class="box">
                        <span class="value">1387</span>
                        <span class="parameter">Likes</span>
                    </div>
                    <div class="box">
                        <span class="value">{}</span>
                        <span class="parameter">Ordered</span>
                    </div>
                </div>
          </div>
                
        """.format(i.image, request.user, i.birthday, ordered)
    else:
        items_div = """
                  <div class="center">
                        <div class="profile">
                            <div class="image">
                                <div class="circle-1"></div>
                                <div class="circle-2"></div>
                                <img src="/media/accounting.png" width="70" height="70" >
                            </div>

                            <div class="name">{}</div>
                            <div class="job">unknown</div>

                            <div class="actions">
                                <button class="btn">Test btn</button>
                                <a class="btn" href="/accounts/logout/">Logout</a>
                            </div>
                        </div>

                        <div class="stats">
                            <div class="box">
                                <span class="value">523</span>
                                <span class="parameter">Posts</span>
                            </div>
                            <div class="box">
                                <span class="value">1387</span>
                                <span class="parameter">Likes</span>
                            </div>
                            <div class="box">
                                <span class="value">{}</span>
                                <span class="parameter">Ordered</span>
                            </div>
                        </div>
                  </div>

                """.format(request.user, ordered)




    return mark_safe(items_div)


