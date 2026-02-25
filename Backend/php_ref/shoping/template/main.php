<!DOCTYPE html>
<html>
  <head>
    <title>Home</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <meta name="robots" content="index,follow">
    <meta name="generator" content="GrapesJS Studio">
    <link rel="stylesheet" href="<?=ASSETSURL. '/' . $themefolder;?>/css/style.css">
  </head>
  <body>

<?php echo view('fshop/'.$themefolder.'/template/header'); ?>
 
<?php echo view($main_content); ?>  
 
<?php echo view('fshop/'.$themefolder.'/template/footer'); ?>

</body>
</html>