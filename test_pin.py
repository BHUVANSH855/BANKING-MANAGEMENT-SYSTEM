from live_pincode_lookup import lookup_pin

for pin in ("110001", "560001", "400001", "600001", "999999"):
    print(pin, "->", lookup_pin(pin))
