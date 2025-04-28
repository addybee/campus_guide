# Files Router Module

This module defines a FastAPI router for handling file-related operations, including uploading, retrieving, updating, and deleting files. It supports both GeoJSON/KML files and image files, with validation and database integration.

---

## Features

1. **MIME Type Validation**:
   - Ensures uploaded files have allowed MIME types (`ALLOWED_MIME_TYPES`).
   - Differentiates between GeoJSON/KML files (`GEO_MIME_TYPES`) and image files.

2. **Duplicate Check**:
   - Prevents uploading files with the same name for the same institution.

3. **File Storage**:
   - Saves files using synchronous I/O in a threadpool.

4. **Database Integration**:
   - Creates, retrieves, updates, and deletes database entries for files using `CRUDService`.

5. **Error Handling**:
   - Raises `HTTPException` for invalid file types, duplicates, or missing files.

---

## Endpoints

### 1. Upload Files
**POST** `/files/`

- **Description**: Handles the upload of multiple files. Validates MIME types, checks for duplicates, saves files, and creates database entries.
- **Parameters**:
  - `files`: List of files uploaded via multipart/form-data.
  - `institution_id`: Institution ID provided as a form field.
  - `db`: Database session dependency.
- **Returns**: `UploadFilesResponse` containing lists of created GeoJSON and image files.

---

### 2. Retrieve File
**GET** `/files/{file_type}/{file_name}`

- **Description**: Retrieves a file (GeoJSON or image) based on its type and name.
- **Parameters**:
  - `file_name`: Name of the file to retrieve.
  - `file_type`: Type of the file (`geo` for GeoJSON, `image` for image).
  - `db`: Database session dependency.
- **Returns**:
  - `JSONResponse` for GeoJSON files (file content as JSON).
  - `FileResponse` for image files (file served as binary).

---

### 3. Update File
**PUT** `/files/{file_type}/{file_name}`

- **Description**: Updates an existing file by replacing it with a new file.
- **Parameters**:
  - `file`: The new file uploaded via multipart/form-data.
  - `file_name`: Name of the file to update.
  - `file_type`: Type of the file (`geo` or `image`).
  - `db`: Database session dependency.
- **Returns**: `UploadedFileInfo` containing details of the updated file.

---

### 4. Delete File
**DELETE** `/files/{file_type}/{file_name}`

- **Description**: Deletes a file (GeoJSON or image) based on its type and name.
- **Parameters**:
  - `file_name`: Name of the file to delete.
  - `file_type`: Type of the file (`geo` or `image`).
  - `db`: Database session dependency.
- **Returns**: A dictionary with a success message.

---

## Dependencies

- **Database Session**: Injected using `Depends(get_session)`.
- **CRUDService**: Handles database operations for files.

---

## Responses

- **Success**:
  - File upload: `UploadFilesResponse` with details of created files.
  - File retrieval: `JSONResponse` or `FileResponse`.
  - File update: `UploadedFileInfo` with updated file details.
  - File deletion: Success message.

- **Errors**:
  - `400 Bad Request`: Invalid file type or duplicate file.
  - `404 Not Found`: File not found on disk.
  - `500 Internal Server Error`: Unexpected errors during file operations.

---


# Institution Router Module

This module defines a FastAPI router for handling institution-related operations, including retrieving, creating, updating, and deleting institutions.

---

## Features

1. **Retrieve Institution**:
   - Fetches an institution by its unique ID.

2. **Create Institution**:
   - Allows creating a new institution with validation to prevent duplicates.

3. **Update Institution**:
   - Updates an existing institution's details.

4. **Delete Institution**:
   - Deletes an institution by its unique ID.

---

## Endpoints

### 1. Retrieve Institution
**GET** `/institution/{institution_id}`

- **Description**: Retrieves an institution by its ID.
- **Parameters**:
  - `institution_id`: The unique ID of the institution.
  - `db`: Database session dependency.
- **Returns**: The institution as `InstitutionGet`.

---

### 2. Create Institution
**POST** `/institution`

- **Description**: Creates a new institution.
- **Parameters**:
  - `institution`: Institution data in the request body.
  - `db`: Database session dependency.
- **Returns**: The created institution as `InstitutionGet`.

---

### 3. Update Institution
**PUT** `/institution/{institution_id}`

- **Description**: Updates an existing institution.
- **Parameters**:
  - `institution_id`: The unique ID of the institution to update.
  - `institution`: Updated institution data in the request body.
  - `db`: Database session dependency.
- **Returns**: The updated institution as `InstitutionGet`.

---

### 4. Delete Institution
**DELETE** `/institution/{institution_id}`

- **Description**: Deletes an institution by its ID.
- **Parameters**:
  - `institution_id`: The unique ID of the institution to delete.
  - `db`: Database session dependency.
- **Returns**: A success message indicating the institution was deleted.

---

## Dependencies

- **Database Session**: Injected using `Depends(get_session)`.
- **CRUDService**: Handles database operations for institutions.

---

## Responses

- **Success**:
  - Retrieve: The institution as `InstitutionGet`.
  - Create: The created institution as `InstitutionGet`.
  - Update: The updated institution as `InstitutionGet`.
  - Delete: A success message.

- **Errors**:
  - `400 Bad Request`: Institution already exists or invalid data.
  - `404 Not Found`: Institution not found.
  - `500 Internal Server Error`: Unexpected errors during operations.

---
