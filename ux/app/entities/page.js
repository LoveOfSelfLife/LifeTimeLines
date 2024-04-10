'use client'

import * as React from 'react';

import { useState, useEffect } from 'react';
import PersonsList from './PersonsList';

export function EntityPage() {
  const [persons, setPersons] = useState([]);
  const [selectedPerson, setSelectedPerson] = useState(null);

  // Fetch all persons
  useEffect(() => {
    console.log('Fetching persons');
    fetch('/api/persons')
      .then(response => response.json())
      .then(data => setPersons(data))
      .catch(error => console.error('Error fetching persons:', error));
  }, []);

  const clearSelectedPerson = () => {
    setSelectedPerson(null);
  };

  // Add or update person
  const savePerson = (person) => {
    const method = person.id ? 'PUT' : 'POST';
    const endpoint = person.id ? `/api/persons/${person.id}` : '/api/persons';

    fetch(endpoint, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(person)
    })
    .then(response => response.json())
    .then(data => {
      setPersons(persons.map(p => (p.id === data.id ? data : p)));
      if (!person.id) setPersons([...persons, data]); // Add new person to list
      setSelectedPerson(null); // Reset selection after saving
    })
    .catch(error => console.error('Error saving person:', error));
  };

  // Delete person
  const deletePerson = (id) => {
    fetch(`/api/persons/${id}`, { method: 'DELETE' })
      .then(() => setPersons(persons.filter(person => person.id !== id)))
      .catch(error => console.error('Error deleting person:', error));
  };

  return (
    <div>
      <PersonsList persons={persons} onSelectPerson={setSelectedPerson} onDeletePerson={deletePerson} />
    </div>
  );
}
export default EntityPage;
