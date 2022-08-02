<!DOCTYPE html>
<html lang="en">
  %include('common/banner.html')
  <head>
    %include('common/standard-inclusions.tpl')
    <title>Thank you</title>
  </head>
  
  <body>
    <div class="page-content">
      %include('common/navbar.tpl')

      <div class="container main-container pt-3">
        <h1 class="mx-auto text-center my-3 caltech-color">
          Thank you!
        </h1>
        <p class="mx-auto col-6 my-5 text-center text-info font-italic">
          %if feedback_url:
          If you experienced any problems or have any suggestions for
          this service, please <a href="{{feedback_url}}">use our feedback form</a> to let us know.
          %end
        </p>
      </div>

      %include('common/footer.tpl')
    </div>
  </body>
</html>
