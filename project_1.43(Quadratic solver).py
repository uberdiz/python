import sympy as sp
def solve_quadratic():
    # Define symbolic variable
    x = sp.symbols('x')

    # Generate coefficients for the quadratic equation as fractions
    a_val = sp.Rational(input("Enter the a number (as a fraction, e.g., 1/2): "))  # Coefficient of x^2
    b_val = sp.Rational(input("Enter the b number (as a fraction, e.g., 1/2): "))  # Coefficient of x
    c_val = sp.Rational(input("Enter the c number (as a fraction, e.g., 1/2): "))  # Constant term

    # Create the quadratic equation
    equation = a_val * x**2 + b_val * x + c_val

    # Factor the quadratic equation
    factored_form = sp.factor(equation)

    # Solve the quadratic equation
    solutions = sp.solve(equation, x)

    # Prepare the output
    problem = f"Quadratic equation: {a_val}x^2 + {b_val}x + {c_val} = 0"
    factored = f"Factored form: {factored_form}"
    exact_solution = f"Exact solutions: {solutions}"

    return problem, factored, exact_solution
def input_quadratic():
    # Define the symbol
    x = sp.symbols('x')
    
    # Get the degree of the quadratic equation
    degree1 = input("Number of terms in the quadratic (1 to 4): ")
    
    # Initialize the quadratic equation with 0
    quad_1 = 0
    
    # Collect the input based on the degree of the equation
    for i in range(1, int(degree1) + 1):
        # Ask if the term has a variable
        has_variable = input(f"Does term {i} have a variable? (y/n): ").lower()
        
        if has_variable == 'y':
            # If it has a variable, ask for coefficient and exponent
            coeff = sp.Rational(input(f"Enter the coefficient of term {i} (as a fraction or integer): "))
            exponent = int(input(f"Enter the exponent of term {i}: "))
            quad_1 += coeff * x**exponent
        elif has_variable == 'n':
            # If it does not have a variable, treat it as a constant
            constant = sp.Rational(input(f"Enter the constant value for term {i} (as a fraction or integer): "))
            quad_1 += constant
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
            return None
    
    return quad_1
def add_quadratic():
    # Get two quadratic equations from the user
    quad_1 = input_quadratic()
    quad_2 = input_quadratic()

    # Ask user whether to add or subtract the equations
    add_or_sub = input("Do you want to add or subtract the two quadratic equations? (add/sub): ").lower()
    
    # Perform the chosen operation (without simplifying or factoring)
    if add_or_sub == 'add':
        result = quad_1 + quad_2
        print(f"The sum of the two quadratic equations is: {result}")
    elif add_or_sub == 'sub':
        result = quad_1 - quad_2
        print(f"The difference of the two quadratic equations is: {result}")
    else:
        print("Invalid choice, please enter 'add' or 'sub'")
        return None
    
    return result
def multiply_quadratic():
        # Get two quadratic equations from the user
    quad_1 = input_quadratic()
    quad_2 = input_quadratic()

    # Perform the chosen operation (without simplifying or factoring)
    result = sp.solve(quad_1 * quad_2)
    print(f"The sum of the two quadratic equations is: {result}")    
    return result
# Main loop for generating and solving problems
while True:
    type = input("Choose a problem type (solve, add (add or subtract), multiply): ").lower()
    if type == "solve":
        expression1 = solve_quadratic()
        print(f"Resulting quadratic equation: {expression1}")
    elif type == "add":
        expression1 = add_quadratic()
        print(f"Resulting quadratic equation: {expression1}")
    else: # type == "multiply"
        expression1 = multiply_quadratic()
        print(f"Resulting quadratic equation: {expression1}")

    # Check if user wants to continue
    continue_prompt = input("\nDo you want to generate another problem? (y/n): ")
    if continue_prompt.lower() != 'y':
        break
