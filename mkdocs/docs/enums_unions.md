# Enums and Unions

```serene
type Color = enum {Red, Green, Blue}

type Red = None		// None is both a type and a value
type Green = None
type Blue = None

type Color2 = union {Red, Green, Blue}

type CreditCard = struct {
	name: String,
	card_number: String,
	security_code: String,
	credit_score: UInt
}

type DebitCard = struct {
	name: String,
	card_number: String,
	security_code: String,
	pin_number: String,
	routing_number: String
}

type Payment = union {CreditCard, DebitCard}

type Option{X} = union {X, None}

function processCardInfo(card: Payment) {
	print "Hello, " card.name
	match (card) {
        is CreditCard -> print "Your credit score is ", myCard.credit_score
        _ -> pass
    }
}

function main() {
	var my_color = Color::Red
	set my_color = Color::Blue
	
	var my_other_color: Color2 = Red
	// same as var my_other_color =  Color2(Red)
	set	my_other_color = Blue
	
	var my_card: Payment = CreditCard {
		name = "Bill Gates",
		card_number = "0000 1111 2222 3333",
		security_code = "1975"
	}
	
	processCardInfo(my_card)
}
```

