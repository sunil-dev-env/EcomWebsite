document.addEventListener('DOMContentLoaded', function() {
    // Automatically hide alert messages after 5 seconds and refresh the page
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
      setTimeout(function() {
        alert.classList.remove('show');
        alert.classList.add('fade');
  
        // Refresh the page after hiding the alert
        setTimeout(function() {
          location.reload();
        }, 1000); // Add a delay before refreshing to ensure alert is hidden
      }, 5000); // Time before hiding the alert
    });
  
    // Additional custom scripts can go here
  });

  document.getElementById('payment_method').addEventListener('change', function() {
    var selectedValue = this.value;
    var creditCardFields = document.getElementById('credit_card_fields');
    
    if (selectedValue === 'card') {
        creditCardFields.style.display = 'block';
    } else {
        creditCardFields.style.display = 'none';
    }
});

// Trigger the change event on page load to ensure the fields are hidden if a different option is pre-selected
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('payment_method').dispatchEvent(new Event('change'));
});

function toggleCustomPrice(selectElement) {
  var customPriceInput = document.getElementById('customPrice');
  if (selectElement.value === 'custom') {
      customPriceInput.style.display = 'block';
      customPriceInput.name = 'price'; // Change the name to price when custom input is shown
  } else {
      customPriceInput.style.display = 'none';
      customPriceInput.name = 'custom_price'; // Change the name to custom_price to avoid conflict
      customPriceInput.value = ''; // Clear the value when hiding
  }
}

// Trigger the function on page load to handle the case where the form is submitted with custom value
document.addEventListener("DOMContentLoaded", function() {
  var priceDropdown = document.getElementById('priceDropdown');
  toggleCustomPrice(priceDropdown);
});