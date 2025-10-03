import tkinter as tk

def on_button_click(button_code):
    """
    This function is called when a button is pressed.
    It prints the unique code of the pressed button to the console.
    
    Args:
        button_code (int): The number associated with the button.
    """
    print(f"Button with code '{button_code}' was pressed.")

def create_main_window():
    """
    Creates and configures the main application window and its widgets.
    """
    # Create the main window instance
    window = tk.Tk()
    window.title("Button Grid")
    
    # Set a minimum size for the window for better layout
    window.minsize(300, 300)

    # --- Create and place the buttons in a 3x3 grid ---
    print("Application started. Press the buttons in the window.")
    
    # Use a loop to create the 9 buttons
    for i in range(9):
        button_code = i + 1
        
        # We use a 'lambda' here to pass the specific 'button_code'
        # to our function. Without it, every button would send the last
        # value of the loop (9).
        button = tk.Button(
            window,
            text=f"Press Me ({button_code})",
            font=("Helvetica", 12),
            command=lambda code=button_code: on_button_click(code)
        )
        
        # Determine the row and column for the button in the grid
        # i // 3 gives the integer division result (0, 1, 2) for the row
        # i % 3 gives the remainder (0, 1, 2) for the column
        row = i // 3
        col = i % 3
        
        # Place the button in the grid and make it expand to fill the cell
        button.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

    # --- Configure grid resizing ---
    # Make the rows and columns expand equally when the window is resized
    for i in range(3):
        window.grid_rowconfigure(i, weight=1)
        window.grid_columnconfigure(i, weight=1)

    # Start the Tkinter event loop. This makes the window appear and
    # wait for user interaction (like button clicks).
    window.mainloop()


# --- Main execution block ---
if __name__ == "__main__":
    create_main_window()