# Phil
An audiophile personal assistant

## What is Phil
Phil is a project made for fun and always will be like that. It is a configurable assistant that reacts to sounds, but unlikely your average personal assistant is designed to react to music.

## Which music?
Phil reacts to notes. To put it simple, take any instrument that is capable of emitting a single note and you can configure Phil to react to that note. I have a digital keyboard that has no USB connection or MIDI connection, and using Phil I can (almost) use it as a (sort of) MIDI controller.

## What can I do?
Up to you. Read the examples and just add to callbacks.py any function you want to execute. Then, on detections.py just map the note to the corresponding function as per example.

## Installation and running

	git clone https://github.com/thecookingsenpai/Phil
	cd Phil
	sh setup.sh
	source run.sh

Phil stays in your tray bar, if need to quit or to edit preferences.

## Example
Let's write a method to be executed on "D" note.
In callbacks.py

	def on_d_note_my_method(note):
		print("Hi! This is " + note)

Now let's add it to the "D" note listener in detections.py

	{
		[...],
		"62": on_d_note,
		[...]
	}

For your convenience, detections.py contains a legend that shows integers to notes.
