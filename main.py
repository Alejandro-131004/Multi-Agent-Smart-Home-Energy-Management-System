import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import asyncio
from agents.initialize_agents import start_agents

def start_agents_gui():
    try:
        # Get input values
        start_date = date_entry.get() or '2015-03-01 14:00:00'
        city = city_entry.get() or 'Madrid'
        num_divisions = int(divisions_entry.get() or 5)
        desired_temperature = float(temp_entry.get() or 40.0)
        
        # Validate date format
        try:
            datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD HH:MM:SS.")
            return
        
        # Close the GUI window
        root.destroy()
        
        # Run agents asynchronously
        asyncio.run(start_agents(
            date=start_date,
            city=city,
            num_divisions=num_divisions,
            desired_temperature=desired_temperature
        ))
        
        print("Agents started successfully!")  # Log success
    except ValueError as e:
        messagebox.showerror("Error", f"Invalid input: {e}")

# Create the main window
root = tk.Tk()
root.title("Start Agents")

# Create and arrange input fields and labels
tk.Label(root, text="Start Date (YYYY-MM-DD HH:MM:SS):").grid(row=0, column=0, padx=10, pady=5, sticky="e")
date_entry = tk.Entry(root, width=25)
date_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="City:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
city_entry = tk.Entry(root, width=25)
city_entry.grid(row=1, column=1, padx=10, pady=5)

tk.Label(root, text="Number of Divisions:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
divisions_entry = tk.Entry(root, width=25)
divisions_entry.grid(row=2, column=1, padx=10, pady=5)

tk.Label(root, text="Desired Temperature:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
temp_entry = tk.Entry(root, width=25)
temp_entry.grid(row=3, column=1, padx=10, pady=5)

# Create and arrange the "Start" button
start_button = tk.Button(root, text="Start Agents", command=start_agents_gui)
start_button.grid(row=4, column=0, columnspan=2, pady=10)

# Run the GUI event loop
root.mainloop()

