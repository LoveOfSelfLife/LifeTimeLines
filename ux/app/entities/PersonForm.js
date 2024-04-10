'use client'
import React, { useState, useEffect } from 'react';

export function PersonForm({ person, onSavePerson, onClearPerson}) {
  const initialFormState = { id: '', name: '', age: '', home: '' };
  const [formData, setFormData] = useState(initialFormState);

  useEffect(() => {
    // Populate form if person is selected for editing
    if (person) setFormData(person);
  }, [person]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSavePerson(formData);
  };
  const handleClear = () => {
    setFormData(initialFormState); // Reset form data
    if (onClearPerson) onClearPerson(); // Call the clear person handler if provided
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="hidden" name="id" value={formData.id} />
      <label>
        Name:
        <input type="text" name="name" value={formData.name} onChange={handleChange} required />
      </label>
      <label>
        Age:
        <input type="number" name="age" value={formData.age} onChange={handleChange} required />
      </label>
      <label>
        Home:
        <input type="text" name="home" value={formData.home} onChange={handleChange} required />
      </label>
      <button type="submit">Save</button>
      <button type="button" onClick={handleClear}>Clear</button>      
    </form>
  );
}
export default PersonForm;

