<!DOCTYPE html>
<html lang="en">
  %include('common/banner.html')
  <head>
    %include('common/standard-inclusions.tpl')
    <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.6.0/css/all.css">
    <title>Add or edit a University of Virginia DIBS entry</title>

  </head>
  
  <body>
    <div class="page-content">
      %include('common/navbar.tpl')
      %from os import stat
      %from os.path import join, exists
      %from commonpy.file_utils import nonempty

      %col_width = "col-5" if item else "col-6"

      <div class="container main-container  mx-auto mt-4">
        <h2 class="mx-auto text-center pb-2">
          %if item:
          Edit item with barcode {{item.barcode}}
          %else:
          Add new item to DIBS
          %end
        </h2>
        <p class="col-10 mx-auto font-italic">
          Note that DIBS does not change the item status in the 
          library catalog. The catalog record should be updated manually
          to reflect the fact that some copies have been pulled from
          circulation and made available via DIBS.
        </p>

        <form id="form" action="{{base_url}}/update/{{action}}" method="POST"
              enctype="multipart/form-data">
          <div class="row">
            <div class="{{col_width}}"><!--left side -->
              <div class="form-group row col-12">
                <label for="barcode" class="col-form-label">
                  Barcode:
                </label>
                <input name="barcode" type="text" class="form-control"
                       placeholder="Barcode number"
                       %if item:
                       value="{{item.barcode}}"
                       %end
                       required autofocus>
              </div>
              <div class="form-group row col-12">
                <label for="duration" class="col-form-label">
                  Loan duration (in hours):
                </label>
                <input name="duration" type="number" class="form-control"
                       placeholder="Number of hours"
                       step="any" min="1"
                       %if item:
                       value="{{item.duration}}"
                       %end
                       required>
              </div>
            </div>
            <div class="{{col_width}}"><!--middle -->
              <div class="form-group row col-12">
                <label for="num_copies" class="col-form-label">
                  Number of copies via DIBS:
                </label>
                <input name="num_copies" type="number" class="form-control"
                       placeholder="Number of copies"
                       step="any" min="1"
                       %if item:
                       value="{{item.num_copies}}"
                       %end
                       required>
              </div>

            </div>

            %if item:
            <div class="col-2 d-flex align-items-center pr-5">
              %thumbnail_url_for_barcode = thumbnails_url_pattern.format(barcode = item.barcode)
              %if item.barcode :
                <img class="mx-auto pt-3 thumbnail-image" style="width: 90px" 
                    src="{{thumbnail_url_for_barcode}}" onerror="this.src='{{base_url}}/static/missing-thumbnail.svg';this.onerror='';">
              %else :
                <img class="mx-auto pt-3 thumbnail-image" style="width: 90px" 
                    src="{{base_url}}/static/missing-thumbnail.svg">
              %end
            </div>
            %end
          </div>
         
          <div class="form-group row col-12">
            <label for="notes" class="form-group control-label my-1">
              Notes (optional, for internal use only):
            </label>
            <textarea name="notes" id="notes" class="form-control py-1 my-0"
                      rows="5" placeholder="Note text">\\
               %if item:
{{item.notes}}\\
               %end
</textarea>
          </div>

          <div class="py-4">
            <div class="btn-toolbar mx-auto" style="width: 240px;">
              <!-- fake input element, to set default action for enter key -->
              <input name="default" value="" type="submit"
                     style="width: 0; height: 0; padding: 0; margin: 0; outline: none; border: 0" />
              <button class="btn btn-secondary mx-2" style="width: 100px; height: 2.5em"
                      name="cancel" value="Cancel" type="submit"
                      formnovalidate>Cancel</button>
              <button id="btnAdd" class="btn btn-primary mx-2" style="width: 100px"
                      name="add" type="submit">
                      %if item:
                      Save
                      %else:
                      Add
                      %end
              </button>
            </div>
          </div>
        </form>
      </div>

      %include('common/footer.tpl')
    </div>
  </body>
</html>
