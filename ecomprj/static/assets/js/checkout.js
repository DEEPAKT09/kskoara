$(document).ready(function () {

    $('.payWithRazorpay').click(function (e) {
        e.preventDefault();


        var first_name = $("[name='first_name']").val();
        var last_name = $("[name='last_name']").val();
        var email = $("[name='email']").val();
        var phone = $("[name='phone']").val();
        var country = $("[name='country']").val();
        var address = $("[name='address']").val();
        var city = $("[name='city']").val();
        var postal_code = $("[name='postal_code']").val();

        if (first_name == "" || last_name == "" || email == "" || phone == "" || country == "" || address == "" || city == "" || postal_code == "") {
            swal("Alert", "All Fields are mandatory!", "error");
            return false;
        }
        else {
            $.ajax({
                method: "GET",
                url: "/checkout",
                success: function (response) {
                    var options = {
                        "key": "rzp_test_NEVlDB9Gc0JaSP", // Enter the Key ID generated from the Dashboard
                        "amount": response.total_price, // Amount is in currency subunits. Default currency is INR. Hence, 50000 refers to 50000 paise
                        "currency": "INR",
                        "name": "KsKoara", //your business name
                        "description": "Test Transaction",
                        "image": "https://example.com/your_logo",
                        // "order_id": "order_9A33XWu170gUtm", //This is a sample Order ID. Pass the `id` obtained in the response of Step 1
                        "handler": function (response) {
                            alert(response.razorpay_payment_id);
                            // alert(response.razorpay_order_id);
                            // alert(response.razorpay_signature)
                        },
                        "prefill": { //We recommend using the prefill parameter to auto-fill customer's contact information, especially their phone number
                            "name": fname + " " + lname, //your customer's name
                            "email": email,
                            "contact": phone  //Provide the customer's phone number for better conversion rates 
                        },
                        "notes": {
                            "address": "Razorpay Corporate Office"
                        },
                        "theme": {
                            "color": "#3399cc"
                        }
                    };
                    var rzp1 = new Razorpay(options);
                    rzp1.open();
                }
            })

        }




    });


});