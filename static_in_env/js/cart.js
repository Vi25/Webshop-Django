var updateBtns = document.getElementsByClassName('update-cart')



for (i = 0; i < updateBtns.length; i++) {
	updateBtns[i].addEventListener('click', function(event){
		var numProductOrder = document.getElementsByClassName('num-product')
		var input = 0;
		if (numProductOrder[0]){
			input = numProductOrder[0].value
			if (isNaN(input) || input <= 0) {
				input = 1;
			}
		}else {
			input = 1;
		}
		var itemId = this.dataset.product
		var action = this.dataset.action

		console.log('itemId:', itemId, 'Action:', action,'numProductOrder',input)
		console.log('USER:', user)

		if (user == 'AnonymousUser'){
			addCookieItem(itemId, action)
		}else{
			updateUserOrder(event,itemId, action,input)
		}
	})
}

function updateUserOrder(event,itemId, action,input){
	console.log('User is authenticated, sending data...')

		var url = '/update_item/'

		fetch(url, {
			method:'POST',
			headers:{
				'Content-Type':'application/json',
				'X-CSRFToken':csrftoken,
				'X-Requested-With': 'XMLHttpRequest',
			},
			body:JSON.stringify({'itemId':itemId, 'action':action,'numProductOrder':input})
		})
		.then((response) => {
		   return response.json();
		})
		.then((data) => {
			var obj = JSON.parse(data);



			console.log('Data1: ', data)
			console.log('Data: ', obj)

			for(i=0; i<obj.length; i++){
				console.log('DataFields '+i+': ',obj[i].quantity)
			}

			updateCart(obj);
			var pathname = window.location.pathname;
			if(pathname == '/order-summary/') {
				updateOrderSummary(obj, itemId);
				var itemExist = false;
				for (i = 0; i < obj.length; i++) {
					if (obj[i].item_id == itemId) {
						itemExist = true;
						break;
					}
				}
				if (action == 'removeall' || itemExist == false) {
					var buttonClicked = event.target
					var itemCount = document.getElementsByClassName('item-count')
					buttonClicked.parentElement.parentElement.parentElement.remove()
					for (var i = 0; i < itemCount.length; i++) {
						itemCount[i].innerText = i + 1;
					}
				}
			}
		});
}


function addCookieItem(itemId, action){
	console.log('User is not authenticated')

	if (action == 'add'){
		if (cart[itemId] == undefined){
		cart[itemId] = {'quantity':1}

		}else{
			cart[itemId]['quantity'] += 1
		}
	}

	if (action == 'remove'){
		cart[itemId]['quantity'] -= 1

		if (cart[itemId]['quantity'] <= 0){
			console.log('Item should be deleted')
			delete cart[itemId];
		}
	}
	if (action == 'removeall'){
			console.log('Item should be deleted')
			delete cart[itemId];

	}
	console.log('CART:', cart)
	document.cookie ='cart=' + JSON.stringify(cart) + ";domain=;path=/"

	location.reload()
}

//recalculated cart
function cartItemCount(data) {
	var cartItemCount = document.querySelectorAll('span');
	Array.from(cartItemCount).forEach(function(el) {
		if(el.classList.contains('cart-item-count')){
			var newCartItemCount = document.createElement('span');
			newCartItemCount.classList.add("cart-item-count", "header-icons-noti");
			newCartItemCount.innerHTML = data.length;
			el.parentNode.replaceChild( newCartItemCount, el );
		}
	})

}

function updateCart(data) {
	var total=0;
	var cartHtml = '';
	for(var i=0; i<data.length; i++){
		if(data[i].item_id__discount_price) {
			total += (data[i].item_id__discount_price * data[i].quantity);
			cartHtml +=
				`<li class="header-cart-item">
				<div class="header-cart-item-img">
					<img src="${data[i].item_id__large_image_url}" style="width: 70px;">
				</div>

				<div class="header-cart-item-txt">
					<a href="#" class="header-cart-item-name">
						${data[i].item_id__title}
					</a>

					<span class="header-cart-item-info">
						
						${data[i].quantity} x  $${data[i].item_id__discount_price}
						
					</span>
				</div>
			</li>`;
		}else {
			total += (data[i].item_id__price * data[i].quantity);
			cartHtml +=
				`<li class="header-cart-item">
				<div class="header-cart-item-img">
					<img src="${data[i].item_id__large_image_url}" style="width: 70px;">
				</div>

				<div class="header-cart-item-txt">
					<a href="#" class="header-cart-item-name">
						${data[i].item_id__title}
					</a>

					<span class="header-cart-item-info">
						
						${data[i].quantity} x $${data[i].item_id__price}
						
					</span>
				</div>
			</li>`;
		}

	}



	var tiniCart = document.querySelectorAll("ul");
	Array.from(tiniCart).forEach(function(el) {
		if(el.classList.contains('tini-cart')){
			var newTiniCart = document.createElement('ul');
			newTiniCart.classList.add("header-cart-wrapitem","tini-cart");
			newTiniCart.innerHTML = cartHtml;
			el.parentNode.replaceChild(newTiniCart,el);

		}
	})
	total = total.toFixed(2);
	document.getElementById('cart-total').innerText = 'Total check: $'+total;
	document.getElementById('cart-total-ss').innerText = 'Total check: $'+total;

	 cartItemCount(data);
}

function updateOrderSummary(data,itemId) {
	var locus,total=0;

	for(var i=0; i<data.length; i++){
		if (data[i].item_id__discount_price)
			total += (data[i].item_id__discount_price * data[i].quantity);
		else
			total += (data[i].item_id__price * data[i].quantity);

		if(data[i].item_id==itemId){
			locus = i;

		}

	}
	if(data[0])
		if(data[0].order_id__coupon_id__amount)
			total -= data[0].order_id__coupon_id__amount;
	total = total.toFixed(2);
	document.getElementById('cell-cart-total').innerHTML =`<b>$${total}</b>`;

	if(data[locus]){
		document.getElementById('quantity-'+itemId).innerText = data[locus].quantity ;
		var itemTotalPrice = document.getElementById('item-total-price-'+itemId);
		if(data[locus].item_id__discount_price){
			itemTotalPrice.innerHTML=` $${data[locus].item_id__discount_price * data[locus].quantity}
               <span class="badge badge-primary">  Saving $${(data[locus].item_id__price - data[locus].item_id__discount_price) * data[locus].quantity}</span>`
		}else
			itemTotalPrice.innerText='$'+ data[locus].item_id__price * data[locus].quantity;
	}


}