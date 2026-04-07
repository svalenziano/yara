Where should files be stored?  In the file system?  In a database?  Some files may be large: e.g. a 65 mb / 600-page pdf

## Idea 0: Crazy simple
No file storage.  User gives Python a filepath that points to a file or folder.  

Python will use that filepath to ingest the files into the DB, but it won't do anything with the original files, since the DB will contain everything we need to know about them.

## Idea 1: File system
Regardless of where files are pulled from, they end up organized inside of a `corpus/` directory at the project root.

Store in "corpus/" directory that is structured similarly to the database.  Users get folders, and projects get folders under each user.  Each user and project has a unique key, generated from the database.
```bash
corpus/
  ├── u-1/
  │   ├── b-1/
  │   │   ├── thing1
  │   │   ├── thing2
  │   │   └── thing3
  │   └── b-2/
  │       ├── thing1
  │       ├── thing2
  │       └── thing3
  └── u-2/
      ├── b-3/
      │   ├── thing1
      │   ├── thing2
      │   └── thing3
      └── b-4/
          ├── thing1
          ├── thing2
          └── thing3
```