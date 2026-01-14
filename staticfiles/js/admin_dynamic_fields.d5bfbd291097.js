document.addEventListener('DOMContentLoaded', function() {
    const contentField = document.querySelector('textarea[name="content"]');
    
    if (contentField) {
        // Create "Add Another Paragraph" button
        const addButton = document.createElement('button');
        addButton.textContent = "Add Another Paragraph";
        addButton.type = "button";
        addButton.style.margin = "10px 0";
        
        // Append the button after the content field
        contentField.parentNode.appendChild(addButton);

        // Add functionality to append another textarea dynamically
        addButton.addEventListener('click', function() {
            const newTextArea = document.createElement('textarea');
            newTextArea.name = "content_extra";
            newTextArea.rows = 3;
            newTextArea.cols = 40;
            newTextArea.placeholder = "Additional Paragraph";

            // Append the new textarea after the button
            addButton.parentNode.insertBefore(newTextArea, addButton.nextSibling);
        });
    }
});
