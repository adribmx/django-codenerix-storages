# -*- coding: utf-8 -*-
#
# django-codenerix-storages
#
# Copyright 2017 Centrologic Computational Logistic Center S.L.
#
# Project URL : http://www.codenerix.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from .models import Storage, StorageBox
from codenerix.models import CodenerixModel
from codenerix_products.models import ProductFinal, ProductUnique


# ############################
class GenCode(CodenerixModel):
    class Meta(CodenerixModel.Meta):
        abstract = True

    code = models.CharField(_("Code"), max_length=64, blank=False, null=False)
    code_counter = models.IntegerField(_("Code counter"), blank=False, null=False, editable=False)

    def setcode(self):

        now = datetime.datetime.now()
        values = {
            'year': now.year,
            'day': now.day,
            'month': now.month,
            'hour': now.hour,
            'minute': now.minute,
            'second': now.second,
            'microsecond': now.microsecond,
            'quarter': now.month // 4 + 1,
            'number': self.code_counter,
        }
        return self.code_format.format(**values)

    def save(self, *args, **kwargs):

        if 'code_format' not in self:
            raise Exception(_('Code format undefined!'))

        with transaction.atomic():
            # Find new code_counter
            model = self._meta.model
            last = model.objects.filter(
                created__gte=timezone.datetime(self.date.year, 1, 1),
                created__lt=timezone.datetime(self.date.year + 1, 1, 1)
            ).order_by("-code_counter").first()

            # Check if we found a result
            if last:
                # Add one more
                self.code_counter = last.code_counter + 1
            else:
                # This is the first one
                self.code_counter = 1

            # Create new code
            self.code = self.setcode()

            # Save
            return super(GenCode, self).save(*args, **kwargs)


# Solicitud de stock entre de almacenes
class RequestStock(GenCode):
    storage_source = models.ForeignKey(Storage, related_name='request_stocks_src', verbose_name=_("Storage source"), null=False, blank=False, on_delete=models.PROTECT)
    storage_destination = models.ForeignKey(Storage, related_name='request_stocks_dst', verbose_name=_("Storage destionation"), null=False, blank=False, on_delete=models.PROTECT)
    request_user = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=False, related_name='request_stocks')
    request_date = models.DateTimeField(_("Request Date"), blank=False, null=False)
    desired_date = models.DateTimeField(_("Desired Date"), blank=False, null=False)

    def __fields__(self, info):
        fields = []
        fields.append(('batch_source', _('Batch source'), 100))
        fields.append(('batch_destination', _('Batch destination'), 100))
        fields.append(('stock_movement_products', _('Products'), 100))
        fields.append(('storage_source', _("Storage source")))
        fields.append(('storage_destination', _("Storage destionation")))
        fields.append(('request_user', _('Request user')))
        fields.append(('request_date', _("Request Date")))
        fields.append(('desired_date', _("Desired Date")))
        return fields

    def __str__(self):
        return u"{} -> {}".format(self.storage_source, self.storage_destination)

    def __unicode__(self):
        return self.__str__()

    def lock_delete(self):
        if self.line_request_stock.exists():
            return _("Cannot delete request stock model, relationship between request stock model and lines")
        if self.outgoing_albarans.exists():
            return _("Cannot delete request stock model, relationship between request stock model and outgoing albaran")
        else:
            return super(RequestStock, self).lock_delete()
    
    def save(self, *args, **kwargs):
        self.code_format = getattr(settings, 'CDNX_STORAGE_CODE_REQUEST_STOCK', 'RS{year}{day}{month}-{hour}{minute}--{number}')
        return super(RequestStock, self).save(*args, **kwargs)


class LineRequestStock(CodenerixModel):
    request_stock = models.ForeignKey(RequestStock, on_delete=models.CASCADE, related_name='line_request_stock', verbose_name=_("Request stock"), null=False, blank=False)
    product_final = models.ForeignKey(ProductFinal, on_delete=models.CASCADE, related_name='line_request_stock', verbose_name=_("Product"), null=False, blank=False)
    quantity = models.FloatField(_("Quantity"), null=False, blank=False)

    def __fields__(self, info):
        fields = []
        fields.append(('product_final', _('Product'), 100))
        fields.append(('quantity', _('Quantity'), 100))
        return fields

    def __str__(self):
        return u"{} ({})".format(self.product_final, self.quantity)

    def __unicode__(self):
        return self.__str__()


class OutgoingAlbaran(GenCode):
    request_stock = models.ForeignKey(RequestStock, on_delete=models.CASCADE, related_name='outgoing_albarans', verbose_name=_("Request stock"), null=False, blank=False)
    prepare_user = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=False, related_name='outgoing_albarans')
    prepare_date = models.DateTimeField(_("Prepare Date"), blank=False, null=False)
    outgoing_date = models.DateTimeField(_("Outgoing Date"), blank=True, null=True)
    estimated_date = models.DateTimeField(_("Estimated Date"), blank=True, null=True)

    def __fields__(self, info):
        fields = []
        fields.append(('request_stock', _("Request stock")))
        fields.append(('prepare_user', _('Prepare user')))
        fields.append(('prepare_date', _("Prepare Date")))
        fields.append(('outgoing_date', _("Outgoing Date")))
        fields.append(('estimated_date', _("Estimated Date")))
        return fields

    def __str__(self):
        return u"{} ({})".format(self.outgoing_date, self.request_stock)

    def __unicode__(self):
        return self.__str__()

    def lock_delete(self):
        if self.line_outgoing_albarans.exists():
            return _("Cannot delete outgoing albaran model, relationship between outgoing albaran model and lines")
        if self.ingoing_albarans.exists():
            return _("Cannot delete outgoing albaran model, relationship between outgoing albaran model and ingoing albaran")
        else:
            return super(OutgoingAlbaran, self).lock_delete()
    
    def save(self, *args, **kwargs):
        self.code_format = getattr(settings, 'CDNX_STORAGE_CODE_OUTGOING_ALBARAN', 'OA{year}{day}{month}-{hour}{minute}--{number}')
        return super(OutgoingAlbaran, self).save(*args, **kwargs)


class LineOutgoingAlbaran(CodenerixModel):
    outgoing_albaran = models.ForeignKey(OutgoingAlbaran, related_name='line_outgoing_albarans', verbose_name=_("Outgoing Albaran"), null=False, blank=False, on_delete=models.CASCADE)
    product_unique = models.ForeignKey(ProductUnique, related_name='line_outgoing_albarans', verbose_name=_("Outgoing Albaran"), null=False, blank=False, on_delete=models.CASCADE)
    prepare_user = models.ForeignKey(User, related_name='line_outgoing_albarans', verbose_name=_("Prepare user"), blank=False, null=False, on_delete=models.CASCADE)
    validator_user = models.ForeignKey(User, related_name='line_outgoing_albarans', verbose_name=_("Validator user"), blank=False, null=False, on_delete=models.CASCADE)
    # box = 1

    def __fields__(self, info):
        fields = []
        fields.append(('outgoing_albaran', _("Outgoing Albaran")))
        fields.append(('product_unique', _("Outgoing Albaran")))
        fields.append(('prepare_user', _("Prepare user")))
        fields.append(('validator_user', _("Validator user")))
        # box = 1
        return fields

    def __str__(self):
        return u"{} ({})".format(self.outgoing_albaran, self.product_unique)

    def __unicode__(self):
        return self.__str__()


class IngoingAlbaran(GenCode):
    outgoing_albaran = models.ForeignKey(OutgoingAlbaran, related_name='ingoing_albarans', verbose_name=_("Outgoing Albaran"), null=False, blank=False, on_delete=models.CASCADE)
    reception_user = models.ForeignKey(User, related_name='ingoing_albarans', verbose_name=_("Reception user"), blank=False, null=False, on_delete=models.CASCADE)
    reception_date = models.DateTimeField(_("Reception Date"), blank=True, null=True)

    def __fields__(self, info):
        fields = []
        fields.append(('outgoing_albaran', _("Outgoing Albaran")))
        fields.append(('reception_user', _("Reception user")))
        fields.append(('reception_date', _("Reception Date")))
        return fields

    def __str__(self):
        return u"{} ({})".format(self.outgoing_albaran, self.reception_user)

    def __unicode__(self):
        return self.__str__()

    def lock_delete(self):
        if self.line_ingoing_albarans.exists():
            return _("Cannot delete ingoing albaran model, relationship between ingoing albaran model and lines")
        else:
            return super(IngoingAlbaran, self).lock_delete()
    
    def save(self, *args, **kwargs):
        self.code_format = getattr(settings, 'CDNX_STORAGE_CODE_INGOING_ALBARAN', 'OI{year}{day}{month}-{hour}{minute}--{number}')
        return super(IngoingAlbaran, self).save(*args, **kwargs)


class LineIngoingAlbaran(CodenerixModel):
    ingoing_albaran = models.ForeignKey(IngoingAlbaran, related_name='line_ingoing_albarans', verbose_name=_("Ingoing Albaran"), null=False, blank=False, on_delete=models.CASCADE)
    box = models.ForeignKey(StorageBox, related_name='line_outgoing_albarans', verbose_name=_("Box"), null=False, blank=False, on_delete=models.CASCADE)
    product_unique = models.ForeignKey(OutgoingAlbaran, related_name='line_outgoing_albarans', verbose_name=_("Product"), null=False, blank=False, on_delete=models.CASCADE)
    quantity = models.FloatField(_("Quantity"), null=False, blank=False)
    validator_user = models.ForeignKey(User, related_name='line_outgoing_albarans', verbose_name=_("Validator user"), blank=False, null=False, on_delete=models.CASCADE)

    def __fields__(self, info):
        fields = []
        fields.append(('ingoing_albaran', _("Ingoing Albaran")))
        fields.append(('box', _("Box")))
        fields.append(('product_unique', _("Product")))
        fields.append(('quantity', _("Quantity")))
        fields.append(('validator_user', _("Validator user")))
        return fields

    def __str__(self):
        return u"{} ({})".format(self.product_unique, self.quantity)

    def __unicode__(self):
        return self.__str__()